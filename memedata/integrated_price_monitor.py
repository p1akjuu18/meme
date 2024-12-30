import asyncio
import logging
import os
import pandas as pd
from datetime import datetime
import aiohttp
from typing import Dict, List, Optional
from support_resistance_analyzer import SupportResistanceAnalyzer
from real_time_update import TokenDataUpdater

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegratedPriceMonitor:
    def __init__(self, telegram_token: str):
        self.telegram_token = telegram_token
        self.base_url = f"https://api.telegram.org/bot{telegram_token}"
        self.chat_ids = set()  # 使用set存储多个chat_id
        
        # 获取桌面路径
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.token_folder = os.path.join(self.desktop_path, "token")
        
        # 初始化组件
        self.support_analyzer = SupportResistanceAnalyzer(self.token_folder)
        self.data_updater = TokenDataUpdater()
        self.price_alerts = {}
        
        # 加载保存的chat_ids
        self.load_chat_ids()

    def load_chat_ids(self):
        """从文件加载保存的chat_ids"""
        try:
            chat_ids_file = "telegram_chat_ids.txt"
            if os.path.exists(chat_ids_file):
                with open(chat_ids_file, "r") as f:
                    self.chat_ids = set(line.strip() for line in f if line.strip())
                logger.info(f"已加载 {len(self.chat_ids)} 个chat_id")
        except Exception as e:
            logger.error(f"加载chat_ids失败: {str(e)}")

    def save_chat_ids(self):
        """保存chat_ids到文件"""
        try:
            with open("telegram_chat_ids.txt", "w") as f:
                for chat_id in self.chat_ids:
                    f.write(f"{chat_id}\n")
        except Exception as e:
            logger.error(f"保存chat_ids失败: {str(e)}")

    async def get_chat_id(self):
        """获取并更新Telegram chat_ids"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/getUpdates"
                async with session.get(url) as response:
                    data = await response.json()
                    
                    if data["ok"] and data["result"]:
                        new_chat_ids = set()
                        for update in data["result"]:
                            if "message" in update and "chat" in update["message"]:
                                chat_id = str(update["message"]["chat"]["id"])
                                new_chat_ids.add(chat_id)
                        
                        # 添加新的chat_ids
                        if new_chat_ids - self.chat_ids:
                            self.chat_ids.update(new_chat_ids)
                            self.save_chat_ids()
                            logger.info(f"新增 {len(new_chat_ids - self.chat_ids)} 个chat_id")
                    else:
                        logger.warning("请先在Telegram中与机器人对话！")
        except Exception as e:
            logger.error(f"获取chat_id失败: {str(e)}")

    async def send_telegram_message(self, message: str) -> bool:
        """发送消息到所有注册的chat_ids"""
        if not self.chat_ids:
            await self.get_chat_id()
            if not self.chat_ids:
                return False

        success = True
        async with aiohttp.ClientSession() as session:
            for chat_id in self.chat_ids:
                try:
                    url = f"{self.base_url}/sendMessage"
                    data = {
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "HTML"
                    }
                    async with session.post(url, data=data) as response:
                        if response.status != 200:
                            success = False
                            logger.error(f"发送消息到{chat_id}失败")
                except Exception as e:
                    success = False
                    logger.error(f"发送消息到{chat_id}失败: {str(e)}")
        
        return success

    async def check_price_alerts(self, token_symbol: str, current_price: float, 
                               support_levels: List[Dict], threshold: float = 0.01):
        """检查价格是否触及支撑位"""
        for level in support_levels:
            # 只处理频次大于1的支撑位
            if level['frequency'] <= 1:
                continue
                
            price_diff = abs(current_price - level['price']) / level['price']
            alert_id = f"{token_symbol}_{level['price']:.8f}"
            
            if price_diff < threshold and alert_id not in self.price_alerts:
                message = (
                    f"🚨 <b>价格接近高频支撑位提醒</b> 🚨\n\n"
                    f"代币: {token_symbol}\n"
                    f"当前价格: {current_price:.8f}\n"
                    f"支撑位: {level['price']:.8f}\n"
                    f"出现频次: {level['frequency']}\n"
                    f"距离: {price_diff*100:.2f}%\n"
                    f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                if await self.send_telegram_message(message):
                    self.price_alerts[alert_id] = datetime.now().timestamp()
                    logger.info(f"已发送价格提醒: {token_symbol} (频次: {level['frequency']})")

    async def price_monitor_loop(self):
        """价格监控循环"""
        while True:
            try:
                for file_name in os.listdir(self.token_folder):
                    if not file_name.endswith('.csv'):
                        continue
                        
                    token_symbol = file_name.replace('.csv', '')
                    df = self.support_analyzer.load_token_data(token_symbol)
                    
                    if df is not None:
                        current_price = df['close'].iloc[-1]
                        support_levels = self.support_analyzer.find_support_levels(df)
                        await self.check_price_alerts(token_symbol, current_price, support_levels)
                
                # 清理24小时前的警报记录
                current_time = datetime.now().timestamp()
                self.price_alerts = {
                    k: v for k, v in self.price_alerts.items() 
                    if current_time - v < 24*3600
                }
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"价格监控出错: {str(e)}")
                await asyncio.sleep(60)

    async def run(self):
        """运行整合监控系统"""
        logger.info("启动整合价格监控系统...")
        logger.info("支撑位警报阈值: 1%")
        
        # 创建两个异步任务
        update_task = asyncio.create_task(self.data_updater.run_updates_async())
        monitor_task = asyncio.create_task(self.price_monitor_loop())
        
        # 同时运行数据更新和价格监控
        await asyncio.gather(update_task, monitor_task)

    async def broadcast_message(self, message: str) -> bool:
        """群发消息给所有注册用户"""
        if not self.chat_ids:
            await self.get_chat_id()
            if not self.chat_ids:
                logger.warning("没有找到任何chat_id，无法发送广播")
                return False

        success = True
        failed_count = 0
        total_count = len(self.chat_ids)
        
        async with aiohttp.ClientSession() as session:
            for chat_id in self.chat_ids:
                try:
                    url = f"{self.base_url}/sendMessage"
                    data = {
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "HTML"
                    }
                    async with session.post(url, data=data) as response:
                        if response.status != 200:
                            failed_count += 1
                            logger.error(f"发送广播到{chat_id}失败")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"发送广播到{chat_id}失败: {str(e)}")
        
        success_count = total_count - failed_count
        logger.info(f"广播消息发送完成: 成功{success_count}个, 失败{failed_count}个")
        return success_count > 0

if __name__ == "__main__":
    # Telegram机器人配置
    TELEGRAM_TOKEN = "7987851125:AAEei6dBYjOZoQt5Ib4d4Wx97laBvSy6Oh4"
    
    # 创建监控系统实例
    monitor = IntegratedPriceMonitor(TELEGRAM_TOKEN)
    
    # 如果只想发送测试广播消息
    if os.getenv('BROADCAST_TEST', 'false').lower() == 'true':
        message = "📢 全体广播：这是一个测试消息，感谢您的支持！"
        asyncio.run(monitor.broadcast_message(message))
    else:
        # 运行完整的监控系统
        asyncio.run(monitor.run()) 