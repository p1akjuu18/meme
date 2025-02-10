import requests
import pandas as pd
from datetime import datetime
import os
import time

class CoinGeckoClient:
    def __init__(self, api_key=None):
        self.base_url = "https://pro-api.coingecko.com/api/v3"
        self.api_key = api_key
        self.headers = {
            'x-cg-pro-api-key': api_key
        } if api_key else {}

    def get_pool_ohlcv(self, network, pool_address, timeframe='minute', aggregate=15, before_timestamp=None, limit=1000):
        """
        获取代币池的OHLCV数据
        
        参数:
            network (str): 网络名称 (如 'solana')
            pool_address (str): 交易池地址
            timeframe (str): 时间周期 ('minute', 'hour', 'day')
            aggregate (int): 聚合数量
            before_timestamp (int): 获取此时间戳之前的数据
            limit (int): 返回的数据条数
        """
        try:
            endpoint = f"/onchain/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
            
            params = {
                'aggregate': aggregate,
                'limit': limit
            }
            
            if before_timestamp:
                params['before_timestamp'] = before_timestamp
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and 'attributes' in data['data'] and 'ohlcv_list' in data['data']['attributes']:
                ohlcv_data = data['data']['attributes']['ohlcv_list']
                df = pd.DataFrame(ohlcv_data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume'
                ])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                # 按时间戳排序
                df = df.sort_values('timestamp', ascending=True)
                return df
            else:
                print(f"API响应格式不正确: {data}")
                return None
            
        except Exception as e:
            print(f"获取OHLCV数据时出错: {str(e)}")
            return None 