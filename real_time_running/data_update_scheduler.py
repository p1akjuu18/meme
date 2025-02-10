import os
import sys
import locale
import codecs

# 设置默认编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

import schedule
import time
import subprocess
from datetime import datetime
import logging
import chardet

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_scheduler.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('DataScheduler')

def detect_file_encoding(file_path):
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            logger.info(f"文件 {file_path} 的编码为: {encoding}")
            return encoding
    except Exception as e:
        logger.error(f"检测文件编码时出错: {str(e)}")
        return 'utf-8'  # 默认返回UTF-8

def safe_read_file(file_path):
    """安全读取文件"""
    try:
        # 首先尝试检测文件编码
        encoding = detect_file_encoding(file_path)
        
        # 尝试使用检测到的编码读取
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except Exception as e:
            logger.error(f"使用检测到的编码 {encoding} 读取失败: {str(e)}")
            
            # 尝试其他常用编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as file:
                        content = file.read()
                        logger.info(f"成功使用 {enc} 编码读取文件")
                        return content
                except Exception:
                    continue
                    
            raise Exception("所有编码尝试都失败了")
    except Exception as e:
        logger.error(f"读取文件时出错: {str(e)}")
        return None

def run_gmgn_data_collection():
    """运行GMGN数据采集程序"""
    try:
        logger.info("开始运行GMGN数据采集...")
        logger.info(f"当前工作目录: {os.getcwd()}")
        logger.info(f"检查run_gmgn_data.py是否存在: {os.path.exists('data_crawling/run_gmgn_data.py')}")
        
        # 使用完整路径运行脚本
        script_path = os.path.join(os.getcwd(), 'data_crawling', 'run_gmgn_data.py')
        logger.info(f"尝试运行脚本: {script_path}")
        
        # 设置环境变量，禁用输出缓冲
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        # 运行命令并捕获输出
        process = subprocess.Popen(
            ['python', '-u', script_path],  # 添加 -u 参数禁用缓冲
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',  # 指定编码
            bufsize=1,  # 行缓冲
            env=env,  # 使用修改后的环境变量
            universal_newlines=True  # 确保文本模式
        )
        
        # 实时输出日志
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"GMGN输出: {output.strip()}")
                # 立即刷新日志
                sys.stdout.flush()
                
        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"GMGN错误: {stderr}")
            
        if process.returncode == 0:
            logger.info("GMGN数据采集完成")
            return True
        else:
            logger.error(f"GMGN数据采集失败，返回码: {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"GMGN数据采集发生异常: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def run_token_info_collection():
    """运行代币信息采集程序"""
    try:
        logger.info("开始运行代币信息采集...")
        logger.info(f"当前工作目录: {os.getcwd()}")
        
        script_path = os.path.join(os.getcwd(), 'data_crawling', 'coingecko_test.py')
        logger.info(f"尝试运行脚本: {script_path}")
        
        # 修改这里，实时显示输出
        process = subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=1
        )
        
        # 实时输出日志
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"CoinGecko输出: {output.strip()}")
                
        return_code = process.poll()
        if return_code == 0:
            logger.info("代币信息采集完成")
            return True
        else:
            logger.error(f"代币信息采集失败，返回码: {return_code}")
            return False
            
    except Exception as e:
        logger.error(f"代币信息采集发生异常: {str(e)}")
        return False

def run_volume_data_cleaning():
    """运行交易量数据清洗程序"""
    try:
        logger.info("开始运行交易量数据清洗...")
        logger.info(f"当前工作目录: {os.getcwd()}")
        logger.info(f"检查volume_data_cleaner.py是否存在: {os.path.exists('data_cleaning/volume_data_cleaner.py')}")
        
        # 使用完整路径运行脚本
        script_path = os.path.join(os.getcwd(), 'data_cleaning', 'volume_data_cleaner.py')
        logger.info(f"尝试运行脚本: {script_path}")
        
        # 运行命令并捕获输出
        process = subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 实时输出日志
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"数据清洗输出: {output.strip()}")
                
        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"数据清洗错误: {stderr}")
            
        if process.returncode == 0:
            logger.info("交易量数据清洗完成")
            return True
        else:
            logger.error(f"交易量数据清洗失败，返回码: {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"交易量数据清洗发生异常: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def run_historical_data_collection():
    """运行历史数据采集程序"""
    try:
        logger.info("开始运行历史数据采集...")
        logger.info(f"当前工作目录: {os.getcwd()}")
        logger.info(f"检查get_historical_data.py是否存在: {os.path.exists('data_crawling/get_historical_data.py')}")
        
        # 使用完整路径运行脚本
        script_path = os.path.join(os.getcwd(), 'data_crawling', 'get_historical_data.py')
        logger.info(f"尝试运行脚本: {script_path}")
        
        # 运行命令并捕获输出
        process = subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 实时输出日志
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"历史数据采集输出: {output.strip()}")
                
        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"历史数据采集错误: {stderr}")
            
        if process.returncode == 0:
            logger.info("历史数据采集完成")
            return True
        else:
            logger.error(f"历史数据采集失败，返回码: {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"历史数据采集发生异常: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def run_token_holding_analysis():
    """运行代币持仓分析程序"""
    try:
        logger.info("开始运行代币持仓分析...")
        logger.info(f"当前工作目录: {os.getcwd()}")
        
        # 1. 首先运行代币地址合并
        logger.info("开始代币地址合并...")
        logger.info(f"检查merge_token_addresses.py是否存在: {os.path.exists('data_cleaning/merge_token_addresses.py')}")
        
        merge_script_path = os.path.join(os.getcwd(), 'data_cleaning', 'merge_token_addresses.py')
        logger.info(f"尝试运行合并脚本: {merge_script_path}")
        
        # 运行合并命令并捕获输出
        process = subprocess.Popen(
            ['python', merge_script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 实时输出日志
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"地址合并输出: {output.strip()}")
                
        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"地址合并错误: {stderr}")
            return False
            
        if process.returncode != 0:
            logger.error(f"代币地址合并失败，返回码: {process.returncode}")
            return False
            
        # 2. 然后运行持仓分析
        logger.info("开始持仓分析...")
        logger.info(f"检查token_holding_analysis.py是否存在: {os.path.exists('data_analysis/token/token_holding_analysis.py')}")
        
        # 使用完整路径运行脚本
        analysis_script_path = os.path.join(os.getcwd(), 'data_analysis', 'token', 'token_holding_analysis.py')
        logger.info(f"尝试运行分析脚本: {analysis_script_path}")
        
        # 运行命令并捕获输出
        process = subprocess.Popen(
            ['python', analysis_script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 实时输出日志
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"持仓分析输出: {output.strip()}")
                
        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"持仓分析错误: {stderr}")
            
        if process.returncode == 0:
            logger.info("代币持仓分析完成")
            return True
        else:
            logger.error(f"代币持仓分析失败，返回码: {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"代币持仓分析发生异常: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def run_data_processing():
    """运行数据处理程序"""
    try:
        logger.info("开始运行数据处理...")
        
        # 运行Excel数据处理
        logger.info("开始处理Excel数据...")
        process = subprocess.Popen(
            ['python', 'data_cleaning/process_excel.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'  # 指定编码
        )
        
        # 实时输出日志
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"Excel处理输出: {output.strip()}")
                
        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"Excel处理错误: {stderr}")
            return False
            
        if process.returncode != 0:
            logger.error(f"Excel数据处理失败，返回码: {process.returncode}")
            return False
            
        # 运行JSON数据处理
        logger.info("开始处理JSON数据...")
        process = subprocess.Popen(
            ['python', 'data_cleaning/process_json.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'  # 指定编码
        )
        
        # 实时输出日志
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"JSON处理输出: {output.strip()}")
                
        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"JSON处理错误: {stderr}")
            
        if process.returncode != 0:
            logger.error(f"JSON数据处理失败，返回码: {process.returncode}")
            return False

        # 运行链接数据处理
        logger.info("开始处理链接数据...")
        process = subprocess.Popen(
            ['python', 'data_cleaning/process_links.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'  # 指定编码
        )
        
        # 实时输出日志
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"链接处理输出: {output.strip()}")
                
        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"链接处理错误: {stderr}")
            
        if process.returncode != 0:
            logger.error(f"链接数据处理失败，返回码: {process.returncode}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"数据处理发生异常: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def run_support_analysis():
    """运行支撑位分析程序"""
    try:
        logger.info("开始运行支撑位分析...")
        logger.info(f"当前工作目录: {os.getcwd()}")
        logger.info(f"检查support_resistance_analyzer.py是否存在: {os.path.exists('data_analysis/token/support_resistance_analyzer.py')}")
        
        # 使用完整路径运行脚本
        script_path = os.path.join(os.getcwd(), 'data_analysis', 'token', 'support_resistance_analyzer.py')
        logger.info(f"尝试运行脚本: {script_path}")
        
        # 运行命令并捕获输出
        process = subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'  # 指定编码
        )
        
        # 实时输出日志
        analysis_complete = False
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"支撑位分析输出: {output.strip()}")
                # 检查是否包含完成标记
                if "支撑位分析完成标记:" in output:
                    analysis_complete = True
                
        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"支撑位分析错误: {stderr}")
            
        if process.returncode == 0 and analysis_complete:
            logger.info("支撑位分析完成")
            return True
        else:
            logger.error(f"支撑位分析失败，返回码: {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"支撑位分析发生异常: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def run_get_token_info():
    """运行获取代币详细信息程序"""
    try:
        logger.info("开始运行获取代币详细信息...")
        logger.info(f"当前工作目录: {os.getcwd()}")
        logger.info(f"检查get_token_info.py是否存在: {os.path.exists('data_crawling/get_token_info.py')}")
        
        # 使用完整路径运行脚本
        script_path = os.path.join(os.getcwd(), 'data_crawling', 'get_token_info.py')
        logger.info(f"尝试运行脚本: {script_path}")
        
        # 运行命令并捕获输出
        process = subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 实时输出日志
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"代币信息获取输出: {output.strip()}")
                
        # 获取错误输出
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"代币信息获取错误: {stderr}")
            
        if process.returncode == 0:
            logger.info("代币详细信息获取完成")
            return True
        else:
            logger.error(f"代币详细信息获取失败，返回码: {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"代币详细信息获取发生异常: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def run_data_update_cycle():
    """运行完整的数据更新周期"""
    try:
        logger.info("开始新的数据更新周期...")
        logger.info(f"当前工作目录: {os.getcwd()}")
        
        # 输出系统信息
        logger.info(f"系统默认编码: {sys.getdefaultencoding()}")
        logger.info(f"文件系统编码: {sys.getfilesystemencoding()}")
        logger.info(f"区域设置: {locale.getpreferredencoding()}")
        
        # 1. 运行GMGN数据采集
        logger.info("开始GMGN数据采集...")
        if not run_gmgn_data_collection():
            logger.error("GMGN数据采集失败，终止后续步骤")
            return
            
        # 2. 运行GMGN数据处理
        logger.info("开始GMGN数据处理...")
        if not run_data_processing():
            logger.error("GMGN数据处理失败，终止后续步骤")
            return

        # 3. 运行代币信息采集 (CoinGecko)
        logger.info("开始代币信息采集...")
        if not run_token_info_collection():
            logger.error("代币信息采集失败，终止后续步骤")
            return
            
        # 4. 运行交易量数据清洗
        logger.info("开始交易量数据清洗...")
        if not run_volume_data_cleaning():
            logger.error("交易量数据清洗失败，终止后续步骤")
            return

        # 5. 运行获取代币详细信息
        logger.info("开始获取代币详细信息...")
        if not run_get_token_info():
            logger.error("获取代币详细信息失败，终止后续步骤")
            return
            
        # 6. 运行代币持仓分析
        logger.info("开始代币持仓分析...")
        if not run_token_holding_analysis():
            logger.error("代币持仓分析失败，终止后续步骤")
            return
            
        # 7. 运行历史数据采集
        logger.info("开始历史数据采集...")
        if not run_historical_data_collection():
            logger.error("历史数据采集失败，终止后续步骤")
            return
            
        logger.info("数据更新周期完成")
            
    except Exception as e:
        logger.error(f"数据更新周期发生异常: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")

def init_directories():
    """初始化必要的目录"""
    try:
        # 创建data目录
        data_dir = os.path.join(os.getcwd(), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"创建data目录: {data_dir}")
        
        # 创建token目录
        token_dir = os.path.join(data_dir, 'token')
        if not os.path.exists(token_dir):
            os.makedirs(token_dir)
            logger.info(f"创建token目录: {token_dir}")
            
        return True
    except Exception as e:
        logger.error(f"创建目录时出错: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def main():
    try:
        logger.info("数据更新调度程序启动")
        
        # 设置4小时间隔
        schedule.every(4).hours.do(run_data_update_cycle)
        
        # 程序启动时立即运行一次
        run_data_update_cycle()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
            
    except Exception as e:
        logger.error(f"主程序运行出错: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 