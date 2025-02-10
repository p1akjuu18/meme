import os
from dotenv import load_dotenv
from real_time_running.telegram_price_alert import TelegramPriceAlert
import json

def init_telegram_bot():
    # 加载环境变量
    load_dotenv()
    
    # 获取Telegram Token
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    if not telegram_token:
        print("错误：未找到TELEGRAM_TOKEN环境变量")
        return
        
    # 初始化TelegramPriceAlert
    telegram_alert = TelegramPriceAlert(telegram_token)
    
    # 添加chat_id
    chat_id = input("请输入chat_id: ")
    telegram_alert.add_chat_id(chat_id)
    
    # 发送测试消息
    test_message = "🔔 Telegram Bot 初始化测试消息"
    telegram_alert.send_alert(test_message)
    
    print("初始化完成！如果你收到了测试消息，说明配置成功。")

if __name__ == "__main__":
    init_telegram_bot() 