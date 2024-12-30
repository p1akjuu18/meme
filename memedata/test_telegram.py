from telegram_price_alert import TelegramPriceAlert
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_telegram_message():
    try:
        # 使用您的bot token
        bot = TelegramPriceAlert("7987851125:AAEei6dBYjOZoQt5Ib4d4Wx97laBvSy6Oh4")
        
        # 先尝试获取chat_id
        logger.info("正在获取chat_id...")
        bot.get_chat_id()
        
        if bot.chat_id:
            logger.info(f"成功获取chat_id: {bot.chat_id}")
            
            # 发送测试消息
            test_message = (
                "🔔 测试消息\n\n"
                "1. 如果您看到这条消息\n"
                "2. 说明机器人设置成功\n"
                f"3. 您的chat_id是: {bot.chat_id}"
            )
            
            success = bot.send_message(test_message)
            if success:
                logger.info("消息发送成功！")
            else:
                logger.error("消息发送失败")
        else:
            logger.error("未能获取chat_id")
            
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    test_telegram_message() 