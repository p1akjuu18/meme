import psutil
import logging
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServerMetricsCollector:
    def __init__(self, metrics_dir: str = "server_metrics"):
        """
        Initialize the server metrics collector
        
        Args:
            metrics_dir (str): Directory to store metrics data
        """
        self.metrics_dir = metrics_dir
        self.ensure_directory_exists()
        
    def ensure_directory_exists(self):
        """Ensure the metrics directory exists"""
        if not os.path.exists(self.metrics_dir):
            os.makedirs(self.metrics_dir)
            logger.info(f"Created metrics directory: {self.metrics_dir}")
    
    def collect_cpu_metrics(self) -> Dict:
        """Collect CPU-related metrics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                'load_avg': os.getloadavg()
            }
        except Exception as e:
            logger.error(f"Error collecting CPU metrics: {str(e)}")
            return {}
    
    def collect_memory_metrics(self) -> Dict:
        """Collect memory-related metrics"""
        try:
            virtual_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()
            return {
                'virtual_memory': {
                    'total': virtual_memory.total,
                    'available': virtual_memory.available,
                    'used': virtual_memory.used,
                    'percent': virtual_memory.percent
                },
                'swap_memory': {
                    'total': swap_memory.total,
                    'used': swap_memory.used,
                    'free': swap_memory.free,
                    'percent': swap_memory.percent
                }
            }
        except Exception as e:
            logger.error(f"Error collecting memory metrics: {str(e)}")
            return {}
    
    def collect_disk_metrics(self) -> Dict:
        """Collect disk-related metrics"""
        try:
            disk_partitions = psutil.disk_partitions()
            disk_metrics = {}
            
            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_metrics[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    }
                except PermissionError:
                    continue
                    
            return disk_metrics
        except Exception as e:
            logger.error(f"Error collecting disk metrics: {str(e)}")
            return {}
    
    def collect_network_metrics(self) -> Dict:
        """Collect network-related metrics"""
        try:
            network_counters = psutil.net_io_counters()
            return {
                'bytes_sent': network_counters.bytes_sent,
                'bytes_recv': network_counters.bytes_recv,
                'packets_sent': network_counters.packets_sent,
                'packets_recv': network_counters.packets_recv,
                'errin': network_counters.errin,
                'errout': network_counters.errout
            }
        except Exception as e:
            logger.error(f"Error collecting network metrics: {str(e)}")
            return {}
    
    def collect_process_metrics(self) -> List[Dict]:
        """Collect metrics for top processes by CPU and memory usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': pinfo['cpu_percent'],
                        'memory_percent': pinfo['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # Sort by CPU usage and get top 10
            return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]
        except Exception as e:
            logger.error(f"Error collecting process metrics: {str(e)}")
            return []
    
    def collect_all_metrics(self) -> Dict:
        """Collect all server metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': self.collect_cpu_metrics(),
            'memory': self.collect_memory_metrics(),
            'disk': self.collect_disk_metrics(),
            'network': self.collect_network_metrics(),
            'top_processes': self.collect_process_metrics()
        }
    
    def save_metrics(self, metrics: Dict):
        """Save metrics to a JSON file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(self.metrics_dir, f'metrics_{timestamp}.json')
            
            with open(filename, 'w') as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Saved metrics to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")
    
    async def run_metrics_collection(self, interval: int = 60):
        """
        Run continuous metrics collection
        
        Args:
            interval (int): Collection interval in seconds
        """
        logger.info(f"Starting metrics collection with {interval}s interval")
        
        while True:
            try:
                metrics = self.collect_all_metrics()
                self.save_metrics(metrics)
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {str(e)}")
                await asyncio.sleep(5)  # Short sleep before retry

if __name__ == "__main__":
    # Create metrics collector
    collector = ServerMetricsCollector()
    
    # Run metrics collection
    asyncio.run(collector.run_metrics_collection())
