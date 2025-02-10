import subprocess
import os
from datetime import datetime
import logging
from pathlib import Path
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 服务器配置
SERVER_CONFIG = {
    'server': '47.76.248.209',
    'username': 'administrator',
    'password': 'xLh9xmiMuic'
}

# 要备份的远程目录
REMOTE_PATH = r'C:\Users\Administrator\Desktop\crypto_monitor_full\data'

def create_bat_file():
    """创建批处理文件用于复制数据"""
    bat_content = f'''
@echo off
net use \\{SERVER_CONFIG['server']} /user:{SERVER_CONFIG['username']} {SERVER_CONFIG['password']}
xcopy "{REMOTE_PATH}" "%~dp0backup" /E /I /Y
net use \\{SERVER_CONFIG['server']} /delete
'''
    bat_path = 'backup.bat'
    with open(bat_path, 'w') as f:
        f.write(bat_content)
    return bat_path

def download_from_server():
    try:
        # 本地保存路径
        local_path = str(Path.home() / "Documents" / "crypto_backup")
        os.makedirs(local_path, exist_ok=True)
        
        # 创建带时间戳的备份文件夹
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(local_path, f'backup_{timestamp}')
        os.makedirs(backup_dir, exist_ok=True)
        
        logger.info(f"开始连接服务器: {SERVER_CONFIG['server']}")
        logger.info(f"开始备份到: {backup_dir}")
        
        # 创建并运行批处理文件
        bat_path = create_bat_file()
        
        # 运行批处理文件
        process = subprocess.Popen(
            bat_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 等待执行完成
        stdout, stderr = process.communicate()
        
        # 删除批处理文件
        os.remove(bat_path)
        
        if process.returncode == 0:
            # 计算总大小
            total_size = sum(
                os.path.getsize(os.path.join(dirpath,filename))
                for dirpath, dirnames, filenames in os.walk(backup_dir)
                for filename in filenames
            )
            total_size_mb = total_size / (1024 * 1024)
            
            logger.info(f"备份完成！")
            logger.info(f"总大小: {total_size_mb:.2f}MB")
            logger.info(f"保存位置: {backup_dir}")
        else:
            logger.error(f"备份失败！错误信息：{stderr}")
        
    except Exception as e:
        logger.error(f"备份过程发生错误: {str(e)}")

if __name__ == "__main__":
    print("这个脚本将备份服务器上的加密货币监控数据")
    print(f"源目录: {REMOTE_PATH}")
    print("数据将保存到你的Documents文件夹中的crypto_backup目录")
    
    response = input("是否开始备份？(y/n): ")
    if response.lower() == 'y':
        download_from_server()
    else:
        print("程序已退出") 