import requests
import time
import os
from datetime import datetime

SERVER_IP = "47.76.248.209"  # 替换为你的服务器IP
CHECK_INTERVAL = 300  # 每5分钟检查一次

def check_server_status():
    try:
        # 检查服务器状态
        response = requests.get(f"http://{SERVER_IP}:9000/status")
        if response.status_code == 200:
            data = response.json()
            print(f"\n[{datetime.now()}] 服务器状态:")
            print(f"CPU 使用率: {data['cpu']}%")
            print(f"内存使用率: {data['memory']}%")
            print("运行中的程序:")
            for app in data['apps']:
                print(f"- {app['name']}: {app['status']}")
        else:
            print(f"\n[{datetime.now()}] 无法获取服务器状态")
    except Exception as e:
        print(f"\n[{datetime.now()}] 连接服务器失败: {str(e)}")

def main():
    print("开始监控服务器状态...")
    print(f"服务器IP: {SERVER_IP}")
    print(f"检查间隔: {CHECK_INTERVAL} 秒")
    
    while True:
        check_server_status()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main() 