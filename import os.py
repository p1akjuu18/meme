import os
import sys
import locale
import codecs
import traceback
from dotenv import load_dotenv
import subprocess
import time
import logging
import schedule
from datetime import datetime, timedelta
import asyncio

# 添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 从项目根目录导入所需模块
from data_analysis.token.support_resistance_analyzer import SupportResistanceAnalyzer
from real_time_running.real_time_update import TokenDataUpdater
from telegram_price_alert import TelegramPriceAlert

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/price_analysis_scheduler.log', encoding='utf-8', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('PriceAnalysisScheduler')

# 设置所有 logger 的默认编码
for handler in logging.root.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.setEncoding('utf-8')

logger.info(f"系统默认编码: {sys.getdefaultencoding()}")
logger.info(f"文件系统编码: {sys.getfilesystemencoding()}")
logger.info(f"本地编码: {locale.getpreferredencoding()}")

class PriceAnalysisScheduler:
    def __init__(self):
        # 初始化文件路径
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.current_dir)
        self.data_folder = os.path.join(self.project_root, "data")
        self.token_folder = os.path.join(self.data_folder, "token")

        # 确保数据文件夹存在
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            logger.info(f"创建 data 文件夹: {self.data_folder}")
        if not os.path.exists(self.token_folder):
            os.makedirs(self.token_folder)
            logger.info(f"创建 token 文件夹: {self.token_folder}")

        # 初始化数据更新器
        self.data_updater = TokenDataUpdater()

        # 初始化 Telegram 提醒
        load_dotenv()
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        if not telegram_token:
            logger.error("未设置 TELEGRAM_TOKEN 环境变量，Telegram 提醒功能将不可用")
            self.telegram_alert = None
        else:
            try:
                self.telegram_alert = TelegramPriceAlert(telegram_token)
                logger.info("Telegram 提醒功能初始化成功")
            except Exception as e:
                logger.error(f"初始化 Telegram 提醒功能失败: {str(e)}")
                self.telegram_alert = None

    def run_price_analysis(self):
        try:
            logger.info("开始价格分析循环...")

            # 更新价格数据
            self.update_data()

            # 支撑位分析
            self.run_support_resistance_analysis()

            logger.info("价格分析循环完成")
        except Exception as e:
            logger.error(f"价格分析循环发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def update_data(self):
        try:
            logger.info("更新价格数据...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.data_updater.run_updates_async())
            logger.info("价格数据更新完成")
        except Exception as e:
            logger.error(f"更新价格数据时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def run_support_resistance_analysis(self):
        try:
            logger.info("开始运行支撑位分析...")
            analyzer = SupportResistanceAnalyzer(self.token_folder)
            results = analyzer.analyze_all_tokens()
            logger.info(f"支撑位分析结果: {results}")

            # 保存结果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.data_folder, f'support_analysis_{timestamp}.csv')
            analyzer.save_analysis_results(results, output_file)
            logger.info(f"支撑位分析结果已保存到: {output_file}")
        except Exception as e:
            logger.error(f"支撑位分析发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def run(self):
        logger.info("价格分析调度程序启动")
        schedule.every(15).minutes.do(self.run_price_analysis)
        self.run_price_analysis()  # 启动时立即运行一次
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    try:
        logger.info("启动价格分析调度程序...")
        scheduler = PriceAnalysisScheduler()
        scheduler.run()
    except Exception as e:
        logger.error(f"主程序运行出错: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
