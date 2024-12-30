import os
import sys
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.expanduser("~"), "Desktop", f"gmgn_log_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)

def check_dependencies():
    """检查必要的依赖是否安装"""
    required_packages = [
        'selenium',
        'pandas',
        'beautifulsoup4',
        'openpyxl'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logging.error(f"缺少必要的依赖包: {', '.join(missing_packages)}")
        logging.info("请使用以下命令安装依赖：")
        logging.info(f"pip install {' '.join(missing_packages)}")
        return False
    return True

def check_chromedriver():
    """检查 ChromeDriver 是否存在"""
    chromedriver_path = '/usr/local/bin/chromedriver'
    if not os.path.exists(chromedriver_path):
        logging.error(f"ChromeDriver 未找到: {chromedriver_path}")
        logging.info("请安装 ChromeDriver 并确保路径正确")
        return False
    return True

def main():
    """主函数"""
    logging.info("开始执行GMGN数据采集程序...")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查 ChromeDriver
    if not check_chromedriver():
        sys.exit(1)
    
    try:
        # 导入 gmgn_data 模块
        import gmgn_data
        logging.info("数据采集完成")
        
    except Exception as e:
        logging.error(f"程序执行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logging.error(f"发生未预期的错误: {str(e)}")
        sys.exit(1) 