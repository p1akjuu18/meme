import requests
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 替换为你的机器人 Token
BOT_TOKEN = "7987851125:AAEei6dBYjOZoQt5Ib4d4Wx97laBvSy6Oh4"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_all_chat_ids():
    """
    获取所有与机器人互动的用户的 chat_id
    """
    try:
        # 调用 getUpdates API
        url = f"{BASE_URL}/getUpdates"
        response = requests.get(url)
        data = response.json()

        # 检查 API 调用是否成功
        if not data["ok"]:
            logger.error("无法获取更新，请检查你的 Token 是否正确。")
            return []

        # 提取所有的 chat_id
        chat_ids = set()
        for result in data["result"]:
            # 确保消息字段存在
            if "message" in result:
                chat_id = result["message"]["chat"]["id"]
                chat_ids.add(chat_id)

        return list(chat_ids)

    except Exception as e:
        logger.error(f"获取 chat_id 时出错: {str(e)}")
        return []

def main():
    # 获取所有 chat_id
    chat_ids = get_all_chat_ids()

    # 打印 chat_id 列表
    if chat_ids:
        logger.info(f"以下是所有的 chat_id：{chat_ids}")
        print("所有的 chat_id：")
        for chat_id in chat_ids:
            print(chat_id)
    else:
        logger.info("没有找到任何 chat_id。请确认用户已与机器人开始对话。")

if __name__ == "__main__":
    main()
