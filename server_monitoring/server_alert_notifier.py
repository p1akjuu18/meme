import logging
import os
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServerAlertNotifier:
    def __init__(self, telegram_token: str):
        """
        Initialize the server alert notifier
        
        Args:
            telegram_token: Telegram bot token for notifications
        """
        self.telegram_token = telegram_token
        self.base_url = f"https://api.telegram.org/bot{telegram_token}"
        self.chat_ids = set()
        self.alert_history = {}
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'service_status': ['failed', 'dead', 'inactive']
        }
        
        # Load saved chat IDs
        self.load_chat_ids()
        
    def load_chat_ids(self):
        """Load saved chat IDs from file"""
        try:
            chat_ids_file = "telegram_chat_ids.txt"
            if os.path.exists(chat_ids_file):
                with open(chat_ids_file, 'r') as f:
                    self.chat_ids = set(line.strip() for line in f if line.strip())
                logger.info(f"Loaded {len(self.chat_ids)} chat IDs")
        except Exception as e:
            logger.error(f"Error loading chat IDs: {str(e)}")
            
    def save_chat_ids(self):
        """Save chat IDs to file"""
        try:
            with open("telegram_chat_ids.txt", "w") as f:
                for chat_id in self.chat_ids:
                    f.write(f"{chat_id}\n")
            logger.info(f"Saved {len(self.chat_ids)} chat IDs")
        except Exception as e:
            logger.error(f"Error saving chat IDs: {str(e)}")
            
    async def get_chat_id(self):
        """Get and update Telegram chat IDs"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/getUpdates"
                async with session.get(url) as response:
                    data = await response.json()
                    
                    if data.get("ok") and data.get("result"):
                        new_chat_ids = set()
                        for update in data["result"]:
                            if "message" in update and "chat" in update["message"]:
                                chat_id = str(update["message"]["chat"]["id"])
                                new_chat_ids.add(chat_id)
                        
                        if new_chat_ids - self.chat_ids:
                            self.chat_ids.update(new_chat_ids)
                            self.save_chat_ids()
                            logger.info(f"Added {len(new_chat_ids - self.chat_ids)} new chat IDs")
        except Exception as e:
            logger.error(f"Error getting chat IDs: {str(e)}")
            
    async def send_alert(self, message: str, alert_type: str = 'info') -> bool:
        """
        Send alert message to all registered chat IDs
        
        Args:
            message: Alert message
            alert_type: Alert type (info/warning/critical)
        """
        if not self.chat_ids:
            await self.get_chat_id()
            if not self.chat_ids:
                logger.warning("No chat IDs available for sending alerts")
                return False
                
        # Add emoji based on alert type
        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨'
        }
        emoji = emoji_map.get(alert_type, 'ℹ️')
        formatted_message = f"{emoji} {message}"
        
        success = True
        async with aiohttp.ClientSession() as session:
            for chat_id in self.chat_ids:
                try:
                    url = f"{self.base_url}/sendMessage"
                    data = {
                        "chat_id": chat_id,
                        "text": formatted_message,
                        "parse_mode": "HTML"
                    }
                    async with session.post(url, data=data) as response:
                        if response.status != 200:
                            success = False
                            logger.error(f"Failed to send alert to chat ID {chat_id}")
                except Exception as e:
                    success = False
                    logger.error(f"Error sending alert to chat ID {chat_id}: {str(e)}")
                    
        return success
        
    def check_performance_alerts(self, performance_data: Dict) -> List[Dict]:
        """Check for performance-related alerts"""
        alerts = []
        
        try:
            # CPU alerts
            if 'cpu' in performance_data:
                cpu_percent = performance_data['cpu'].get('current')
                if cpu_percent and cpu_percent > self.alert_thresholds['cpu_percent']:
                    alerts.append({
                        'type': 'critical',
                        'message': f"High CPU Usage Alert!\nCurrent: {cpu_percent:.1f}%\nThreshold: {self.alert_thresholds['cpu_percent']}%"
                    })
                    
            # Memory alerts
            if 'memory' in performance_data:
                memory_percent = performance_data['memory'].get('current')
                if memory_percent and memory_percent > self.alert_thresholds['memory_percent']:
                    alerts.append({
                        'type': 'critical',
                        'message': f"High Memory Usage Alert!\nCurrent: {memory_percent:.1f}%\nThreshold: {self.alert_thresholds['memory_percent']}%"
                    })
                    
            # Disk alerts
            if 'disk' in performance_data:
                for mount, data in performance_data['disk'].items():
                    if data.get('current', 0) > self.alert_thresholds['disk_percent']:
                        alerts.append({
                            'type': 'warning',
                            'message': f"High Disk Usage Alert!\nMount: {mount}\nUsage: {data['current']:.1f}%\nThreshold: {self.alert_thresholds['disk_percent']}%"
                        })
                        
        except Exception as e:
            logger.error(f"Error checking performance alerts: {str(e)}")
            
        return alerts
        
    def check_service_alerts(self, service_data: Dict) -> List[Dict]:
        """Check for service-related alerts"""
        alerts = []
        
        try:
            status = service_data.get('status', '').lower()
            if status in self.alert_thresholds['service_status']:
                alerts.append({
                    'type': 'critical',
                    'message': f"Service Status Alert!\nService: {service_data.get('name')}\nStatus: {status}\nDetails: {service_data.get('details', 'No details available')}"
                })
        except Exception as e:
            logger.error(f"Error checking service alerts: {str(e)}")
            
        return alerts
        
    def check_process_alerts(self, process_data: Dict) -> List[Dict]:
        """Check for process-related alerts"""
        alerts = []
        
        try:
            status = process_data.get('status', '').lower()
            if status in ['zombie', 'dead']:
                alerts.append({
                    'type': 'warning',
                    'message': f"Process Status Alert!\nPID: {process_data.get('pid')}\nName: {process_data.get('name')}\nStatus: {status}"
                })
        except Exception as e:
            logger.error(f"Error checking process alerts: {str(e)}")
            
        return alerts
        
    async def process_alerts(self, alerts: List[Dict]):
        """Process and send alerts with cooldown handling"""
        current_time = datetime.now().timestamp()
        
        for alert in alerts:
            alert_key = f"{alert['type']}_{alert['message']}"
            
            # Check if alert is in cooldown
            if alert_key in self.alert_history:
                last_sent = self.alert_history[alert_key]
                # Use different cooldown periods based on alert type
                cooldown = 3600 if alert['type'] == 'critical' else 7200  # 1 hour for critical, 2 hours for others
                
                if current_time - last_sent < cooldown:
                    continue
                    
            # Send alert and update history
            if await self.send_alert(alert['message'], alert['type']):
                self.alert_history[alert_key] = current_time
                
    def set_alert_threshold(self, metric: str, value: float):
        """Update alert threshold for a specific metric"""
        if metric in self.alert_thresholds:
            self.alert_thresholds[metric] = value
            logger.info(f"Updated {metric} threshold to {value}")
            
    async def monitor_and_alert(self, performance_data: Dict, service_data: Optional[Dict] = None, process_data: Optional[Dict] = None):
        """Monitor metrics and send alerts when thresholds are exceeded"""
        try:
            alerts = []
            
            # Check different types of alerts
            alerts.extend(self.check_performance_alerts(performance_data))
            
            if service_data:
                alerts.extend(self.check_service_alerts(service_data))
                
            if process_data:
                alerts.extend(self.check_process_alerts(process_data))
                
            # Process and send alerts
            await self.process_alerts(alerts)
            
        except Exception as e:
            logger.error(f"Error in monitor_and_alert: {str(e)}")

if __name__ == "__main__":
    # Example usage
    TOKEN = os.getenv('TELEGRAM_TOKEN', '')
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set")
        exit(1)
        
    notifier = ServerAlertNotifier(TOKEN)
    
    # Test alert
    asyncio.run(notifier.send_alert("Server monitoring system initialized", "info"))
