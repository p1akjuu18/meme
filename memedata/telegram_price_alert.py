import asyncio
import logging
import os
import pandas as pd
from datetime import datetime
import aiohttp
from typing import Dict, List, Optional
from support_resistance_analyzer import SupportResistanceAnalyzer
from real_time_update import TokenDataUpdater
import requests
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramPriceAlert:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_ids = set()  # 使用set存储多个chat_id
        
        # 获取桌面路径并构建token文件夹路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        token_folder = os.path.join(desktop_path, "token")
        
        # 确保文件夹存在
        if not os.path.exists(token_folder):
            os.makedirs(token_folder)
            logger.info(f"创建文件夹: {token_folder}")
            
        self.support_analyzer = SupportResistanceAnalyzer(token_folder)
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

    def get_chat_id(self) -> None:
        """获取用户的chat_id"""
        try:
            # 调用 getUpdates API
            url = f"{self.base_url}/getUpdates"
            response = requests.get(url)
            data = response.json()

            # 检查 API 调用是否成功
            if not data["ok"]:
                logger.error("无法获取更新，请检查你的 Token 是否正确。")
                return

            # 提取所有的 chat_id
            chat_ids = set()
            for result in data["result"]:
                # 确保消息字段存在
                if "message" in result:
                    chat_id = result["message"]["chat"]["id"]
                    chat_ids.add(chat_id)

            if chat_ids:
                self.chat_ids = chat_ids
                logger.info(f"成功获取chat_ids: {self.chat_ids}")
                
                # 保存chat_id到文件中
                with open("chat_id.txt", "w") as f:
                    for chat_id in self.chat_ids:
                        f.write(f"{chat_id}\n")
            else:
                logger.warning("没有找到任何 chat_id。请确认用户已与机器人开始对话。")
                
        except Exception as e:
            logger.error(f"获取chat_id失败: {str(e)}")

    def send_message(self, message: str) -> bool:
        """发送消息到Telegram"""
        # 如果没有chat_id，尝试获取
        if not self.chat_ids:
            self.get_chat_id()  # 改成同步调用
            if not self.chat_ids:
                return False
            
        try:
            success = True
            for chat_id in self.chat_ids:
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, data=data)
                if response.status_code != 200:
                    success = False
                    logger.error(f"发送消息到{chat_id}失败")
        except Exception as e:
            success = False
            logger.error(f"发送消息失败: {str(e)}")
        return success

    async def monitor_prices(self, check_interval: int = 900):
        """持续监控价格（与real_time_update同步，每15分钟更新一次）"""
        logger.info("开始价格监控...")
        logger.info("设置报警阈值: 1%")
        logger.info("更新间隔: 15分钟")
        
        while True:
            try:
                for file_name in os.listdir(self.support_analyzer.data_folder):
                    if not file_name.endswith('.csv'):
                        continue
                        
                    token_symbol = file_name.replace('.csv', '')
                    df = self.support_analyzer.load_token_data(token_symbol)
                    
                    if df is not None:
                        current_price = df['close'].iloc[-1]
                        support_levels = self.support_analyzer.find_support_levels(df)
                        
                        # 检查价格提醒（移除await）
                        self.check_price_alerts(
                            token_symbol, 
                            current_price, 
                            support_levels,
                            threshold=0.01
                        )
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"监控过程中出错: {str(e)}")
                await asyncio.sleep(60)

    def check_price_alerts(self, token_symbol: str, current_price: float, 
                          support_levels: List[Dict], threshold: float = 0.01) -> None:
        """检查价格是否接近支撑位并发送提醒"""
        for level in support_levels:
            # 只处理频次大于1的支撑位
            if level['frequency'] <= 1:
                continue
            
            price_diff = abs(current_price - level['price']) / level['price']
            
            # 生成警报的唯一标识
            alert_id = f"{token_symbol}_{level['price']:.8f}"
            
            # 如果价格接近支撑位（1%以内）且之前没有发送过警报
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
                
                if self.send_message(message):
                    # 记录已发送的警报
                    self.price_alerts[alert_id] = time.time()
                    logger.info(f"已发送价格提醒: {token_symbol} (频次: {level['frequency']})")
            
            # 如果价格远离支撑位，清除之前的警报记录
            elif price_diff >= threshold and alert_id in self.price_alerts:
                del self.price_alerts[alert_id]

async def main():
    # Telegram机器人配置
    TOKEN = "7987851125:AAEei6dBYjOZoQt5Ib4d4Wx97laBvSy6Oh4"
    
    # 创建价格提醒实例
    alert_system = TelegramPriceAlert(TOKEN)
    
    # 开始监控价格
    await alert_system.monitor_prices()

if __name__ == "__main__":
    asyncio.run(main()) 