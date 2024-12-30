from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime
import time
import logging
import argparse
from bs4 import BeautifulSoup
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GMGNCrawler:
    def __init__(self):
        self.url = "https://gmgn.ai/meme/OKNWW0Bi?chain=sol&tab=complete"
        self.data = []
        self.retry_count = 3
    
    def create_driver(self):
        """创建新的driver实例"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # 添加更多反检测参数
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--disable-extensions")
        options.add_argument('--disable-infobars')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 添加代理（如果需要）
        # options.add_argument('--proxy-server=http://your_proxy_ip:port')
        
        # 设置更真实的 User-Agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # 执行反检测 JavaScript
            stealth_js = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
            window.navigator.chrome = {runtime: {}};
            """
            driver.execute_script(stealth_js)
            
            return driver
        except Exception as e:
            logging.error(f"创建driver失败: {str(e)}")
            raise e

    def start_crawler(self):
        driver = None
        try:
            driver = self.create_driver()
            driver.set_page_load_timeout(60)
            
            logging.info("开始访问页面...")
            
            # 先访问主页
            driver.get("https://gmgn.ai")
            time.sleep(3)
            
            # 再访问目标页面
            driver.get(self.url)
            time.sleep(5)
            
            # 模拟人类行为
            driver.execute_script("window.scrollTo(0, 200)")
            time.sleep(1)
            
            logging.info("等待表格加载...")
            
            # 等待表格容器
            table = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.g-table-body"))
            )
            
            # 模拟滚动
            driver.execute_script("arguments[0].scrollIntoView(true);", table)
            time.sleep(2)
            
            # 等待数据行出现
            rows = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.g-table-body tr:not(.g-table-placeholder)"))
            )
            
            logging.info(f"找到 {len(rows)} 行数据")
            
            # 处理数据行
            for index, row in enumerate(rows, 1):
                try:
                    cells = row.find_elements(By.CSS_SELECTOR, "td.g-table-cell")
                    
                    if len(cells) >= 14:
                        row_data = {
                            "symbol": cells[0].get_attribute("textContent").strip(),
                            "time": cells[1].get_attribute("textContent").strip(),
                            "volume": cells[2].get_attribute("textContent").strip(),
                            "volume_value": cells[3].get_attribute("textContent").strip(),
                            "holders": cells[4].get_attribute("textContent").strip(),
                            "trades": cells[5].get_attribute("textContent").strip(),
                            "volume_1h": cells[6].get_attribute("textContent").strip(),
                            "price": cells[7].get_attribute("textContent").strip(),
                            "change_1m": cells[8].get_attribute("textContent").strip(),
                            "change_5m": cells[9].get_attribute("textContent").strip(),
                            "change_1h": cells[10].get_attribute("textContent").strip(),
                            "security": cells[11].get_attribute("textContent").strip(),
                            "dev": cells[12].get_attribute("textContent").strip(),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        logging.info(f"Row {index} data: {row_data['symbol']}")
                        self.data.append(row_data)
                        
                        # 模拟人类行为，随机暂停
                        time.sleep(random.uniform(0.1, 0.3))
                        
                except Exception as e:
                    logging.error(f"处理第 {index} 行数据时出错: {str(e)}")
                    continue
            
            self.save_data()
            
        except Exception as e:
            logging.error(f"爬虫运行出错: {str(e)}")
            if driver:
                try:
                    # 保存页面源码和截图
                    with open(f"error_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    driver.save_screenshot(f"error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    logging.info("已保存错误页面源码和截图")
                except:
                    pass
            raise e
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def save_data(self):
        try:
            df = pd.DataFrame(self.data)
            filename = f"gmgn_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            logging.info(f"数据已保存到 {filename}")
        except Exception as e:
            logging.error(f"保存数据时出错: {str(e)}")

    def run_continuous(self, interval=60):
        retry_count = 0
        max_retries = 3
        
        while True:
            try:
                if retry_count >= max_retries:
                    logging.error(f"连续失败{max_retries}次，等待较长时间后重试...")
                    time.sleep(300)  # 等待5分钟
                    retry_count = 0
                
                self.data = []  # 清空之前的数据
                self.start_crawler()
                
                if self.data:  # 如果成功获取数据
                    retry_count = 0
                    logging.info(f"等待 {interval} 秒后进行下一次抓取...")
                    time.sleep(interval)
                else:
                    retry_count += 1
                    logging.warning(f"未获取到数据，这是第 {retry_count} 次重试")
                    time.sleep(10)
                    
            except KeyboardInterrupt:
                logging.info("程序已手动停止")
                break
            except Exception as e:
                retry_count += 1
                logging.error(f"运行出错: {str(e)}")
                time.sleep(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=60, help="抓取间隔(秒)")
    parser.add_argument("--process-id", type=str, default="1", help="进程ID")
    args = parser.parse_args()
    
    crawler = GMGNCrawler()
    crawler.run_continuous(interval=args.interval) 