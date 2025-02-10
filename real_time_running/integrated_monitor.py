import os
import time
import logging
from datetime import datetime
import pandas as pd
from data_analysis.token.support_resistance_analyzer import SupportResistanceAnalyzer
from telegram_price_alert import TelegramPriceAlert
import schedule

class IntegratedMonitor:
    def __init__(self):
        # 获取桌面路径
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.data_folder = os.path.join(self.desktop_path, "token1")
        
        # 初始化分析器和告警系统
        self.analyzer = SupportResistanceAnalyzer(self.data_folder)
        self.telegram_alert = TelegramPriceAlert(
            token="7987851125:AAEei6dBYjOZoQt5Ib4d4Wx97laBvSy6Oh4"
        )
        
        # 存储每个代币的支撑位和上次提醒时间
        self.token_data = {}
        
    def initialize_monitoring(self):
        """
        初始化监控：计算所有代币的初始支撑位
        """
        logger.info("初始化价格监控系统...")
        self.update_support_levels()
        
    def update_support_levels(self):
        """
        更新所有代币的支撑位
        """
        try:
            total_files = len([f for f in os.listdir(self.data_folder) if f.endswith('.csv')])
            logger.info(f"开始更新支撑位数据 - 共 {total_files} 个代币")
            processed = 0
            
            for file_name in os.listdir(self.data_folder):
                if not file_name.endswith('.csv'):
                    continue
                    
                token_symbol = file_name.replace('.csv', '')
                df = self.analyzer.load_token_data(token_symbol)
                
                if df is not None:
                    # 计算支撑位
                    support_levels = self.analyzer.find_support_levels(df)
                    current_price = df['close'].iloc[-1]
                    
                    # 更新存储的数据
                    if token_symbol not in self.token_data:
                        self.token_data[token_symbol] = {
                            'support_levels': support_levels,
                            'last_price': current_price,
                            'last_alert_time': {},  # 每个支撑位的最后提醒时间
                            'alert_cooldown': 3600  # 提醒冷却时间（秒）
                        }
                    else:
                        self.token_data[token_symbol]['support_levels'] = support_levels
                        self.token_data[token_symbol]['last_price'] = current_price
                    
                    processed += 1
                    if processed % 10 == 0:  # 每处理10个代币输出一次进度
                        progress = (processed / total_files) * 100
                        logger.info(f"更新进度: {progress:.1f}% ({processed}/{total_files})")
                    
            logger.info(f"支撑位数据更新完成 - 成功处理 {processed} 个代币")
                    
        except Exception as e:
            logger.error(f"更新支撑位数据时出错: {str(e)}")

    def check_price_alerts(self):
        """
        检查所有代币的价格是否触及支撑位
        """
        current_time = time.time()
        alerts_sent = 0
        tokens_checked = 0
        
        logger.info("开始检查价格预警...")
        
        for token_symbol, data in self.token_data.items():
            try:
                df = self.analyzer.load_token_data(token_symbol)
                if df is None:
                    continue
                
                current_price = df['close'].iloc[-1]
                tokens_checked += 1
                
                # 检查每个支撑位
                for level in data['support_levels']:
                    price_diff = abs(current_price - level) / level
                    
                    # 如果价格接近支撑位（距离小于5%）
                    if price_diff < 0.05:
                        # 检查是否在冷却期内
                        last_alert = data['last_alert_time'].get(level, 0)
                        if current_time - last_alert > data['alert_cooldown']:
                            message = (
                                f"🚨 价格接近支撑位提醒 🚨\n\n"
                                f"代币: {token_symbol}\n"
                                f"当前价格: {current_price:.8f}\n"
                                f"支撑位: {level:.8f}\n"
                                f"距离: {price_diff*100:.2f}%\n"
                                f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            )
                            
                            if self.telegram_alert.send_message(message):
                                # 更新最后提醒时间
                                data['last_alert_time'][level] = current_time
                                alerts_sent += 1
                
            except Exception as e:
                logger.error(f"检查 {token_symbol} 价格预警时出错: {str(e)}")
        
        if alerts_sent > 0:
            logger.info(f"价格预警检查完成 - 已发送 {alerts_sent} 条预警")
        else:
            logger.info(f"价格预警检查完成 - 检查了 {tokens_checked} 个代币，无需发送预警")

    def run(self):
        """
        运行监控程序
        """
        logger.info("价格监控系统启动...")
        
        # 初始化
        self.initialize_monitoring()
        
        # 设置定时任务
        schedule.every(15).minutes.do(self.update_support_levels)
        schedule.every(1).minutes.do(self.check_price_alerts)
        
        logger.info("定时任务已设置 - 每15分钟更新支撑位，每1分钟检查预警")
        
        # 运行循环
        while True:
            try:
                schedule.run_pending()
                time.sleep(10)  # 每10秒检查一次定时任务
            except Exception as e:
                logger.error(f"监控系统运行出错: {str(e)}")
                time.sleep(60)  # 出错后等待1分钟再继续

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'  # 简化日志格式
    )
    logger = logging.getLogger(__name__)
    
    # 创建并运行监控器
    monitor = IntegratedMonitor()
    monitor.run() 