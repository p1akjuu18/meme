import logging
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    def __init__(self, metrics_dir: str = "server_metrics"):
        """
        Initialize the performance analyzer
        
        Args:
            metrics_dir: Directory containing metrics data
        """
        self.metrics_dir = metrics_dir
        self.analysis_cache = {}
        
    def load_metrics(self, hours: int = 24) -> List[Dict]:
        """Load metrics from the last specified hours"""
        try:
            metrics = []
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=hours)
            
            # List all metric files
            for filename in os.listdir(self.metrics_dir):
                if not filename.endswith('.json'):
                    continue
                    
                file_path = os.path.join(self.metrics_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        timestamp = datetime.fromisoformat(data['timestamp'])
                        
                        if timestamp >= cutoff_time:
                            metrics.append(data)
                except Exception as e:
                    logger.error(f"Error reading metric file {filename}: {str(e)}")
                    
            return sorted(metrics, key=lambda x: x['timestamp'])
        except Exception as e:
            logger.error(f"Error loading metrics: {str(e)}")
            return []
            
    def analyze_cpu_performance(self, metrics: List[Dict]) -> Dict:
        """Analyze CPU performance trends"""
        try:
            cpu_data = [m['cpu']['cpu_percent'] for m in metrics if 'cpu' in m]
            if not cpu_data:
                return {}
                
            analysis = {
                'current': cpu_data[-1],
                'average': np.mean(cpu_data),
                'max': np.max(cpu_data),
                'min': np.min(cpu_data),
                'trend': 'stable'
            }
            
            # Analyze trend
            if len(cpu_data) > 1:
                recent_avg = np.mean(cpu_data[-5:])
                overall_avg = np.mean(cpu_data[:-5])
                
                if recent_avg > overall_avg * 1.1:
                    analysis['trend'] = 'increasing'
                elif recent_avg < overall_avg * 0.9:
                    analysis['trend'] = 'decreasing'
                    
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing CPU performance: {str(e)}")
            return {}
            
    def analyze_memory_performance(self, metrics: List[Dict]) -> Dict:
        """Analyze memory usage trends"""
        try:
            memory_data = [
                m['memory']['virtual_memory']['percent'] 
                for m in metrics if 'memory' in m
            ]
            if not memory_data:
                return {}
                
            analysis = {
                'current': memory_data[-1],
                'average': np.mean(memory_data),
                'max': np.max(memory_data),
                'min': np.min(memory_data),
                'trend': 'stable'
            }
            
            # Analyze trend
            if len(memory_data) > 1:
                recent_avg = np.mean(memory_data[-5:])
                overall_avg = np.mean(memory_data[:-5])
                
                if recent_avg > overall_avg * 1.1:
                    analysis['trend'] = 'increasing'
                elif recent_avg < overall_avg * 0.9:
                    analysis['trend'] = 'decreasing'
                    
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing memory performance: {str(e)}")
            return {}
            
    def analyze_disk_performance(self, metrics: List[Dict]) -> Dict:
        """Analyze disk usage trends"""
        try:
            disk_analysis = {}
            
            if not metrics or 'disk' not in metrics[-1]:
                return {}
                
            # Analyze each mount point
            for mount_point in metrics[-1]['disk'].keys():
                usage_data = [
                    m['disk'][mount_point]['percent']
                    for m in metrics
                    if 'disk' in m and mount_point in m['disk']
                ]
                
                if not usage_data:
                    continue
                    
                disk_analysis[mount_point] = {
                    'current': usage_data[-1],
                    'average': np.mean(usage_data),
                    'max': np.max(usage_data),
                    'min': np.min(usage_data),
                    'trend': 'stable'
                }
                
                # Analyze trend
                if len(usage_data) > 1:
                    recent_avg = np.mean(usage_data[-5:])
                    overall_avg = np.mean(usage_data[:-5])
                    
                    if recent_avg > overall_avg * 1.05:
                        disk_analysis[mount_point]['trend'] = 'increasing'
                    elif recent_avg < overall_avg * 0.95:
                        disk_analysis[mount_point]['trend'] = 'decreasing'
                        
            return disk_analysis
        except Exception as e:
            logger.error(f"Error analyzing disk performance: {str(e)}")
            return {}
            
    def analyze_network_performance(self, metrics: List[Dict]) -> Dict:
        """Analyze network performance trends"""
        try:
            if not metrics or 'network' not in metrics[-1]:
                return {}
                
            # Calculate network throughput
            throughput_data = []
            for i in range(1, len(metrics)):
                if 'network' not in metrics[i] or 'network' not in metrics[i-1]:
                    continue
                    
                current = metrics[i]['network']
                previous = metrics[i-1]['network']
                
                try:
                    timestamp_current = datetime.fromisoformat(metrics[i]['timestamp'])
                    timestamp_previous = datetime.fromisoformat(metrics[i-1]['timestamp'])
                    time_diff = (timestamp_current - timestamp_previous).total_seconds()
                    
                    if time_diff > 0:
                        bytes_sent = (current['bytes_sent'] - previous['bytes_sent']) / time_diff
                        bytes_recv = (current['bytes_recv'] - previous['bytes_recv']) / time_diff
                        
                        throughput_data.append({
                            'timestamp': timestamp_current,
                            'bytes_sent': bytes_sent,
                            'bytes_recv': bytes_recv
                        })
                except Exception as e:
                    logger.error(f"Error calculating network throughput: {str(e)}")
                    
            if not throughput_data:
                return {}
                
            # Analyze throughput
            sent_data = [d['bytes_sent'] for d in throughput_data]
            recv_data = [d['bytes_recv'] for d in throughput_data]
            
            analysis = {
                'bytes_sent': {
                    'current': sent_data[-1],
                    'average': np.mean(sent_data),
                    'max': np.max(sent_data),
                    'min': np.min(sent_data)
                },
                'bytes_received': {
                    'current': recv_data[-1],
                    'average': np.mean(recv_data),
                    'max': np.max(recv_data),
                    'min': np.min(recv_data)
                }
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing network performance: {str(e)}")
            return {}
            
    def analyze_performance(self, hours: int = 24) -> Dict:
        """
        Perform comprehensive performance analysis
        
        Args:
            hours: Number of hours of data to analyze
        """
        try:
            metrics = self.load_metrics(hours)
            if not metrics:
                logger.warning("No metrics data available for analysis")
                return {}
                
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'period_hours': hours,
                'cpu': self.analyze_cpu_performance(metrics),
                'memory': self.analyze_memory_performance(metrics),
                'disk': self.analyze_disk_performance(metrics),
                'network': self.analyze_network_performance(metrics)
            }
            
            # Cache the analysis
            self.analysis_cache = analysis
            
            logger.info("Completed performance analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Error performing performance analysis: {str(e)}")
            return {}
            
    def get_performance_summary(self) -> str:
        """Generate a human-readable performance summary"""
        try:
            analysis = self.analysis_cache
            if not analysis:
                analysis = self.analyze_performance()
                
            if not analysis:
                return "No performance data available"
                
            summary = []
            summary.append("=== Server Performance Summary ===")
            
            # CPU Summary
            if 'cpu' in analysis and analysis['cpu']:
                cpu = analysis['cpu']
                summary.append("\nCPU Performance:")
                summary.append(f"Current: {cpu['current']:.1f}%")
                summary.append(f"Average: {cpu['average']:.1f}%")
                summary.append(f"Trend: {cpu['trend']}")
                
            # Memory Summary
            if 'memory' in analysis and analysis['memory']:
                mem = analysis['memory']
                summary.append("\nMemory Usage:")
                summary.append(f"Current: {mem['current']:.1f}%")
                summary.append(f"Average: {mem['average']:.1f}%")
                summary.append(f"Trend: {mem['trend']}")
                
            # Disk Summary
            if 'disk' in analysis and analysis['disk']:
                summary.append("\nDisk Usage:")
                for mount, data in analysis['disk'].items():
                    summary.append(f"\n{mount}:")
                    summary.append(f"Current: {data['current']:.1f}%")
                    summary.append(f"Trend: {data['trend']}")
                    
            # Network Summary
            if 'network' in analysis and analysis['network']:
                net = analysis['network']
                summary.append("\nNetwork Performance:")
                if 'bytes_sent' in net:
                    sent = net['bytes_sent']
                    summary.append(f"Send Rate: {sent['current']/1024:.1f} KB/s")
                if 'bytes_received' in net:
                    recv = net['bytes_received']
                    summary.append(f"Receive Rate: {recv['current']/1024:.1f} KB/s")
                    
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {str(e)}")
            return "Error generating performance summary"

if __name__ == "__main__":
    # Create analyzer instance
    analyzer = PerformanceAnalyzer()
    
    # Generate and print performance summary
    print(analyzer.get_performance_summary())
