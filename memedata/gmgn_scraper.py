import requests
import json
import time
import random
from typing import Optional, Dict, List
from proxy_manager import ProxyManager
from monitoring import ScraperMonitor
import logging
import pandas as pd

class GMGNScraperImproved:
    def __init__(self):
        # 初始化日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化代理管理器
        self.proxy_manager = ProxyManager()
        
        # 初始化监控器
        self.monitor = ScraperMonitor()
        
        # User-Agent池
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        # 基础配置
        self.base_url = "https://api.gmgn.ai/v1"
        self.request_interval = random.uniform(2, 5)
        self.max_retries = 3
        self.is_running = False  # 添加运��状态标志
        
    def get_headers(self) -> Dict[str, str]:
        """生成请求头"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive'
        }
        
    def make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """发送请求并处理响应"""
        self.monitor.total_requests += 1
        
        for attempt in range(self.max_retries):
            try:
                proxy = self.proxy_manager.get_proxy()
                response = requests.get(
                    f"{self.base_url}/{endpoint}",
                    headers=self.get_headers(),
                    params=params,
                    proxies=proxy,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # 速率限制
                    self.handle_rate_limit()
                    continue
                else:
                    self.logger.error(f"请求失败: {response.status_code}")
                    if proxy:
                        self.proxy_manager.mark_proxy_failed(proxy)
                    
            except Exception as e:
                self.logger.error(f"请求异常: {str(e)}")
                self.monitor.fail_count += 1
                if proxy:
                    self.proxy_manager.mark_proxy_failed(proxy)
                
            time.sleep(self.request_interval)
            
        return None
        
    def get_market_data(self) -> Optional[List[Dict]]:
        """获取市场数据"""
        params = {
            "chain": "sol",
            "period": "24h",
            "sort": "volume",
            "order": "desc"
        }
        
        data = self.make_request("markets", params)
        if data:
            self.save_data(data)
            return data
        return None
        
    def save_data(self, data: List[Dict]):
        """保存数据"""
        try:
            df = pd.DataFrame(data)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            df.to_csv(f'gmgn_data_{timestamp}.csv', index=False, encoding='utf-8-sig')
            self.logger.info(f"数据已保存到 gmgn_data_{timestamp}.csv")
        except Exception as e:
            self.logger.error(f"保存数据失败: {str(e)}")
            
    def handle_rate_limit(self):
        """处理速率限制"""
        wait_time = random.uniform(30, 60)
        self.logger.warning(f"触发速率限制，等待 {wait_time} 秒")
        time.sleep(wait_time)
        
    def stop(self):
        """安全终止爬虫"""
        self.logger.info("正在终止爬虫...")
        self.is_running = False
        
    def run(self, max_iterations=None):
        """运行爬虫
        Args:
            max_iterations: 最大运行次数，None 表示无限运行
        """
        self.logger.info("开始运行爬虫...")
        self.is_running = True
        iteration = 0
        
        try:
            while self.is_running:
                if max_iterations and iteration >= max_iterations:
                    self.logger.info(f"达到最大运行次数 {max_iterations}，终止爬虫")
                    break
                
                data = self.get_market_data()
                if data:
                    self.logger.info(f"成功获取数据 (第 {iteration + 1} 次)")
                else:
                    self.logger.warning(f"获取数据失败 (第 {iteration + 1} 次)")
                
                self.monitor.check_health()
                time.sleep(self.request_interval)
                iteration += 1
                
        except KeyboardInterrupt:
            self.logger.info("收到终止信号")
        except Exception as e:
            self.logger.error(f"爬虫运行异常: {str(e)}")
        finally:
            self.is_running = False
            self.logger.info(f"爬虫已安全终止，共运行 {iteration} 次")

if __name__ == "__main__":
    scraper = GMGNScraperImproved()
    try:
        # 运行爬虫
        scraper.run()
    except KeyboardInterrupt:
        # 按 Ctrl+C 终止
        scraper.stop()