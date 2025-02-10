import os
import sys
import locale
import codecs
import traceback
import time
import logging
from datetime import datetime
import chardet
import subprocess

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

# 在设置Python路径后导入项目模块
from data_analysis.token.support_resistance_analyzer import SupportResistanceAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/analysis_scheduler.log', encoding='utf-8', mode='a'),
        logging.FileHandler('logs/analysis_scheduler_error.log', encoding='utf-8', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 设置所有logger的默认编码
for handler in logging.root.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.setEncoding('utf-8')
        if 'error' in handler.baseFilename:
            handler.setLevel(logging.ERROR)
        else:
            handler.setLevel(logging.DEBUG)
    elif isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.DEBUG)

logger = logging.getLogger('AnalysisScheduler')

class AnalysisScheduler:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.current_dir)
        self.data_folder = os.path.join(self.project_root, "data")
        
        # 确保data文件夹存在
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            logger.info(f"创建data文件夹: {self.data_folder}")
        
        # 确保token文件夹存在
        self.token_folder = os.path.join(self.data_folder, "token")
        if not os.path.exists(self.token_folder):
            os.makedirs(self.token_folder)
            logger.info(f"创建token文件夹: {self.token_folder}")

    def analyze_support_resistance(self):
        """运行支撑位分析"""
        print("1. 正在进行支撑位分析...")
        
        try:
            # 检查token文件夹是否存在
            token_folder = os.path.join(self.data_folder, "token")
            if not os.path.exists(token_folder):
                print(f"   错误：找不到token文件夹")
                return False
                
            # 检查token文件夹中是否有文件
            if not os.listdir(token_folder):
                print("   错误：token文件夹为空")
                return False
            
            analyzer = SupportResistanceAnalyzer(token_folder)
            results = analyzer.analyze_all_tokens()
            
            if results is None or len(results) == 0:
                print("   错误：分析结果为空")
                return False
            
            # 保存支撑位分析结果（带时间戳）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.data_folder, f"support_resistance_results_{timestamp}.csv")
            analyzer.save_analysis_results(results, output_path)
            print(f"   支撑位分析完成，分析了 {len(results)} 个代币")
            return True
            
        except Exception as e:
            print("   支撑位分析失败！")
            print(f"   错误详情: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def analyze_token_price(self):
        """运行代币价格分析"""
        print("2. 正在进行代币价格分析...")
        logger.info("开始代币价格分析...")
        try:
            from data_analysis.token.token_price_analysis import analyze_token_data
            token_folder = os.path.join(self.data_folder, "token")
            price_results = analyze_token_data(token_folder, output_folder=self.data_folder)
            
            if price_results is None or price_results.empty:
                print("   警告：价格分析结果为空")
                logger.warning("价格分析结果为空DataFrame")
                return False
            
            print("   代币价格分析完成")
            return True
                
        except Exception as e:
            print("   价格分析过程中出错")
            logger.error(f"执行价格分析时发生错误: {str(e)}")
            return False

    def merge_desktop_files(self):
        """运行桌面文件合并"""
        print("3. 正在合并桌面文件...")
        logger.info("开始运行桌面文件合并...")
        merge_script_path = os.path.join(os.getcwd(), 'merge_desktop_files.py')
        if not os.path.exists(merge_script_path):
            print("   错误：找不到合并脚本文件")
            return False
            
        try:
            process = subprocess.Popen(
                ['python', merge_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"   {output.strip()}")
                    logger.info(f"桌面文件合并输出: {output.strip()}")
                    
            _, stderr = process.communicate()
            if stderr:
                logger.error(f"桌面文件合并错误: {stderr}")
                return False
                
            if process.returncode == 0:
                print("   桌面文件合并完成")
                logger.info("桌面文件合并完成")
                return True
            else:
                print(f"   合并失败，返回码: {process.returncode}")
                logger.error(f"桌面文件合并失败，返回码: {process.returncode}")
                return False
                
        except Exception as e:
            print("   合并过程发生异常")
            logger.error(f"桌面文件合并发生异常: {str(e)}")
            return False

    def run_analysis(self):
        """运行完整的分析流程"""
        try:
            print("\n=== 开始新的分析循环 ===")
            logger.info("开始新的分析循环...")
            
            # 1. 运行支撑位分析
            logger.debug("准备执行支撑位分析...")
            support_result = self.analyze_support_resistance()
            logger.debug(f"支撑位分析结果: {support_result}")
            
            # 2. 运行代币价格分析
            logger.debug("准备执行代币价格分析...")
            price_result = self.analyze_token_price()
            logger.debug(f"代币价格分析结果: {price_result}")
            
            # 3. 运行桌面文件合并
            logger.debug("准备执行桌面文件合并...")
            merge_result = self.merge_desktop_files()
            logger.debug(f"桌面文件合并结果: {merge_result}")
            
            print("=== 分析循环完成 ===\n")
            logger.info("分析周期完成")
            
        except Exception as e:
            print(f"=== 分析循环出错: {str(e)} ===")
            logger.error(f"分析循环发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def run(self):
        """启动调度程序"""
        logger.info("分析调度程序启动")
        
        while True:
            try:
                # 运行一次完整的分析循环
                self.run_analysis()
                
                # 在循环完成后等待900秒
                print("\n等待900秒后开始下一次分析...\n")
                time.sleep(900)
                
            except Exception as e:
                print(f"\n执行过程中发生错误: {str(e)}")
                logger.error(f"运行循环时发生错误: {str(e)}")
                logger.error(traceback.format_exc())
                # 发生错误时也等待900秒再继续
                print("\n等待900秒后重试...\n")
                time.sleep(900)

def main():
    try:
        logger.info("分析调度程序启动")
        
        # 创建调度器实例
        scheduler = AnalysisScheduler()
        scheduler.run()
            
    except Exception as e:
        logger.error(f"主程序运行出错: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 