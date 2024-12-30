from pycoingecko import CoinGeckoAPI
import pandas as pd
from datetime import datetime
import os
import time
import requests

class HistoricalDataFetcher:
    def __init__(self):
        self.cg = CoinGeckoAPI(api_key="CG-dJ6UcnVr8yvqw5Cvm8CywKvD")

    def get_token_info(self, network, address):
        """
        获取代币的详细信息
        """
        try:
            headers = {
                'x-cg-pro-api-key': "CG-dJ6UcnVr8yvqw5Cvm8CywKvD"
            }
            
            base_url = "https://pro-api.coingecko.com/api/v3"
            endpoint = f"{base_url}/onchain/networks/{network}/tokens/{address}/info"
            
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and 'attributes' in data['data']:
                attributes = data['data']['attributes']
                return {
                    'description': attributes.get('description', ''),
                    'websites': attributes.get('websites', []),
                    'twitter_handle': attributes.get('twitter_handle', ''),
                    'telegram_handle': attributes.get('telegram_handle', '')
                }
            return None
            
        except Exception as e:
            print(f"获取代币信息时出错: {str(e)}")
            return None

    def get_pool_ohlcv(self, network, pool_address, timeframe='minute', aggregate=15, before_timestamp=None, limit=1000):
        """
        获取代币池的OHLCV数据
        """
        try:
            headers = {
                'x-cg-pro-api-key': "CG-dJ6UcnVr8yvqw5Cvm8CywKvD"
            }
            
            base_url = "https://pro-api.coingecko.com/api/v3"
            
            params = {
                'aggregate': aggregate,
                'limit': limit
            }
            
            if before_timestamp:
                params['before_timestamp'] = before_timestamp
            
            endpoint = f"{base_url}/onchain/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
            
            response = requests.get(endpoint, headers=headers, params=params)
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
                print(f"API响应: {data}")
                return None
            
        except Exception as e:
            print(f"获取池OHLCV数据时出错: {str(e)}")
            return None

def process_pools():
    # 获取桌面路径
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    
    # 创建token文件夹
    token_folder = os.path.join(desktop_path, 'token')
    os.makedirs(token_folder, exist_ok=True)
    
    try:
        # 读取Excel文件
        excel_path = os.path.join(desktop_path, 'token_query_results_all_20250108_205910_cleaned.xlsx')
        df = pd.read_excel(excel_path)
        
        # 打印列名，用于调试
        print("Excel文件中的列名:", df.columns.tolist())
        
        # 处理代币地址，删除'solana_'前缀
        df['代币地址'] = df['代币地址'].str.replace('solana_', '')
        
        fetcher = HistoricalDataFetcher()
        
        # 创建新的列来存储额外信息
        df['description'] = ''
        df['websites'] = ''
        df['twitter_handle'] = ''
        df['telegram_handle'] = ''
        
        # 遍历每个交易池
        for index, row in df.iterrows():
            try:
                token_address = row['代币地址']
                pool_address = row['交易池_地址']  # 使用正确的列名
                symbol = row['符号']
                
                if pd.isna(pool_address) or pd.isna(symbol) or pd.isna(token_address):
                    continue
                    
                print(f"正在处理 {symbol} 的数据...")
                
                # 获取代币额外信息（使用代币地址）
                token_info = fetcher.get_token_info('solana', token_address)
                if token_info:
                    df.at[index, 'description'] = token_info['description']
                    df.at[index, 'websites'] = ', '.join(token_info['websites']) if token_info['websites'] else ''
                    df.at[index, 'twitter_handle'] = token_info['twitter_handle']
                    df.at[index, 'telegram_handle'] = token_info['telegram_handle']
                
                # 获取K线数据（使用交易池地址）
                pool_data = fetcher.get_pool_ohlcv(
                    network='solana',
                    pool_address=pool_address,
                    timeframe='minute',
                    aggregate=15,
                    limit=1000
                )
                
                if pool_data is not None:
                    # 使用简单的文件名（只用符号）
                    filename = f"{symbol}.csv"
                    file_path = os.path.join(token_folder, filename)
                    
                    # 保存数据（不包含索引）
                    pool_data.to_csv(file_path, index=False)
                    print(f"已保存 {symbol} 的数据到: {filename}")
                    print(f"数据时间范围: {pool_data['timestamp'].min()} 到 {pool_data['timestamp'].max()}")
                
                # 添加延时避免请求过快
                time.sleep(1)
                
            except Exception as e:
                print(f"处理行 {index} 时出错: {str(e)}")
                continue
                
        # 保存更新后的Excel文件
        output_excel_path = os.path.join(desktop_path, 'token_info_updated.xlsx')
        df.to_excel(output_excel_path, index=False)
        print(f"已保存更新后的代币信息到: {output_excel_path}")
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")

if __name__ == "__main__":
    process_pools() 