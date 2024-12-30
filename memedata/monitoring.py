import logging
import smtplib
from email.mime.text import MIMEText
from typing import Optional, Dict, List

class ScraperMonitor:
    def __init__(self):
        self.alert_threshold = 50  # 失败率阈值
        self.fail_count = 0
        self.total_requests = 0
        self.logger = logging.getLogger(__name__)
        
        # 邮件配置
        self.email_config: Optional[Dict] = None
        
    def configure_email(self, smtp_server: str, smtp_port: int, 
                       sender: str, password: str, receivers: List[str]):
        """配置邮件告警"""
        self.email_config = {
            'server': smtp_server,
            'port': smtp_port,
            'sender': sender,
            'password': password,
            'receivers': receivers
        }
        
    def check_health(self):
        """检查爬虫健康状态"""
        if self.total_requests == 0:
            return
            
        fail_rate = (self.fail_count / self.total_requests) * 100
        if fail_rate > self.alert_threshold:
            message = f"爬虫失败率过高: {fail_rate:.2f}%"
            self.send_alert(message)
            
    def send_alert(self, message: str):
        """发送告警"""
        self.logger.warning(message)
        
        if self.email_config:
            try:
                msg = MIMEText(message)
                msg['Subject'] = '爬虫告警通知'
                msg['From'] = self.email_config['sender']
                msg['To'] = ','.join(self.email_config['receivers'])
                
                with smtplib.SMTP(self.email_config['server'], 
                                self.email_config['port']) as server:
                    server.login(self.email_config['sender'], 
                               self.email_config['password'])
                    server.send_message(msg)
                    
            except Exception as e:
                self.logger.error(f"发送告警邮件失败: {str(e)}")