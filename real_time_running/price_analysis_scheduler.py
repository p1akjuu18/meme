import os
import sys
import locale
import codecs
import traceback
import time
import logging
from datetime import datetime
import pandas as pd
from real_time_running.real_time_update import TokenDataUpdater

# 设置默认编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/price_analysis_scheduler.log', encoding='utf-8', mode='a'),
        logging.FileHandler('logs/price_analysis_scheduler_error.log', encoding='utf-8', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('PriceAnalysisScheduler')

class PriceAnalysisScheduler:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.current_dir)
        self.data_folder = os.path.join(self.project_root, "data")
        
        # 确保data文件夹存在
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        
        # 确保token文件夹存在
        self.token_folder = os.path.join(self.data_folder, "token")
        if not os.path.exists(self.token_folder):
            os.makedirs(self.token_folder)
            
        self.data_updater = TokenDataUpdater()
        
        # 创建或加载更新记录Excel
        self.log_file = os.path.join(self.data_folder, "update_logs.xlsx")
        if os.path.exists(self.log_file):
            self.logs_df = pd.read_excel(self.log_file)
        else:
            self.logs_df = pd.DataFrame(columns=['时间', '状态', '详情'])

    def save_log(self, status: str, details: str = ""):
        """保存更新记录到Excel"""
        new_log = pd.DataFrame({
            '时间': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            '状态': [status],
            '详情': [details]
        })
        self.logs_df = pd.concat([self.logs_df, new_log], ignore_index=True)
        self.logs_df.to_excel(self.log_file, index=False)

    def update_price_data(self):
        """更新价格数据"""
        print("正在更新价格数据...")
        
        try:
            print("正在调用数据更新方法...")
            self.data_updater.run_updates()
            print("价格数据更新完成")
            self.save_log("成功", "价格数据更新完成")
            return True
        except Exception as e:
            error_msg = f"价格数据更新失败: {str(e)}"
            print(error_msg)
            self.save_log("失败", error_msg)
            logger.error(traceback.format_exc())
            return False

    def run_analysis(self):
        """运行更新流程"""
        try:
            print("\n=== 开始数据更新 ===")
            
            # 更新价格数据
            update_result = self.update_price_data()
            
            print("=== 更新循环完成 ===\n")
            
        except Exception as e:
            error_msg = f"更新循环出错: {str(e)}"
            print(f"=== {error_msg} ===")
            self.save_log("错误", error_msg)
            logger.error(traceback.format_exc())

    def run(self):
        """启动更新程序"""
        print("价格更新程序启动")
        self.save_log("启动", "价格更新程序启动")
        
        while True:
            try:
                # 运行一次完整的更新循环
                self.run_analysis()
                
                # 在循环完成后等待900秒
                print("\n等待900秒后开始下一次更新...\n")
                time.sleep(900)
                
            except Exception as e:
                error_msg = f"执行过程中发生错误: {str(e)}"
                print(f"\n{error_msg}")
                self.save_log("错误", error_msg)
                logger.error(traceback.format_exc())
                print("\n等待900秒后重试...\n")
                time.sleep(900)

def main():
    try:
        scheduler = PriceAnalysisScheduler()
        scheduler.run()
            
    except Exception as e:
        logger.error(f"主程序运行出错: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 