from pycoingecko import CoinGeckoAPI
import pandas as pd
from datetime import datetime, timedelta
import os
import time
import requests

# CoinGecko API配置
COINGECKO_API_KEY = "CG-dJ6UcnVr8yvqw5Cvm8CywKvD"

def get_latest_filtered_results():
    """获取最新的token_data_sorted文件"""
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"错误：未找到数据文件夹: {data_dir}")
        return None

    # 查找token_data_sorted开头的文件
    result_files = [f for f in os.listdir(data_dir) if f.startswith('token_data_sorted_') and f.endswith('.xlsx')]
    if not result_files:
        print("错误：未找到token_data_sorted文件")
        return None

    # 按文件名排序（因为文件名包含时间戳）
    latest_file = sorted(result_files)[-1]
    return os.path.join(data_dir, latest_file)

class HistoricalDataFetcher:
    def __init__(self):
        self.cg = CoinGeckoAPI(api_key=COINGECKO_API_KEY)

    def get_pool_ohlcv(self, network, pool_address, timeframe='minute', aggregate=15, before_timestamp=None, limit=1000, days_limit=None):
        """
        获取代币池的OHLCV数据
        
        Args:
            days_limit: 如果设置，则只获取最近指定天数的数据
        """
        try:
            headers = {
                'x-cg-pro-api-key': COINGECKO_API_KEY
            }
            
            base_url = "https://pro-api.coingecko.com/api/v3"
            
            all_data = []
            current_timestamp = int(datetime.now().timestamp())
            
            # 如果设置了天数限制，计算起始时间戳
            if days_limit:
                earliest_allowed_timestamp = int((datetime.now() - timedelta(days=days_limit)).timestamp())
            
            while True:
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
                    if not ohlcv_data:  # 如果没有更多数据了
                        break
                        
                    # 如果设置了天数限制，检查是否已经达到时间限制
                    if days_limit:
                        filtered_data = [item for item in ohlcv_data if item[0] >= earliest_allowed_timestamp]
                        all_data.extend(filtered_data)
                        
                        # 如果当前批次的数据已经超过了时间限制，就不再继续获取
                        if any(item[0] < earliest_allowed_timestamp for item in ohlcv_data):
                            break
                    else:
                        all_data.extend(ohlcv_data)
                    
                    # 获取最早的时间戳作为下一次请求的before_timestamp
                    earliest_timestamp = min(item[0] for item in ohlcv_data)
                    before_timestamp = earliest_timestamp
                    
                    print(f"已获取 {len(all_data)} 条数据，继续获取更早的数据...")
                    
                    # 添加延时避免请求过快
                    time.sleep(1)
                else:
                    print(f"API响应: {data}")
                    break
            
            if all_data:
                df = pd.DataFrame(all_data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume'
                ])
                
                # 转换时间戳为正常格式
                df = convert_to_utc8(df)
                
                # 按时间戳排序
                df = df.sort_values('timestamp', ascending=True)
                
                print(f"总数据时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
                print(f"总数据条数: {len(df)} 行")
                
                return df
            return None
            
        except Exception as e:
            print(f"获取池OHLCV数据时出错: {str(e)}")
            return None

def process_pools():
    """处理代币池数据"""
    try:
        # 获取最新的filtered结果文件
        input_file = get_latest_filtered_results()
        if not input_file:
            print("未找到可处理的文件")
            return None
            
        print(f"\n正在处理文件: {input_file}")
        df = pd.read_excel(input_file)
        
        # 创建data目录（如果不存在）
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)
        
        # 创建token文件夹在data目录下
        token_folder = os.path.join(data_dir, 'token')
        os.makedirs(token_folder, exist_ok=True)
        
        # 打印列名，用于调试
        print("Excel文件中的列名:", df.columns.tolist())
        
        # 处理代币地址，删除'solana_'前缀
        df['代币地址'] = df['代币地址'].str.replace('solana_', '')
        
        fetcher = HistoricalDataFetcher()
        
        # 遍历每个交易池
        for index, row in df.iterrows():
            try:
                token_address = row['代币地址']
                pool_address = row['交易池_地址']
                token_name = row['币种']
                days_alive = row['代币存活天数']
                
                if pd.isna(pool_address) or pd.isna(token_name) or pd.isna(token_address):
                    continue

                # 检查是否已存在该代币的CSV文件
                filename = f"{token_name}.csv"
                file_path = os.path.join(token_folder, filename)
                if os.path.exists(file_path):
                    print(f"{token_name} 的历史数据文件已存在，跳过处理")
                    continue
                    
                print(f"\n开始处理 {token_name} 的数据...")
                
                # 根据存活天数决定获取数据的时间范围
                days_limit = 100 if days_alive > 100 else None
                if days_limit:
                    print(f"{token_name} 存活天数为 {days_alive}天，将只获取最近{days_limit}天的数据")
                
                # 获取历史K线数据
                pool_data = fetcher.get_pool_ohlcv(
                    network='solana',
                    pool_address=pool_address,
                    timeframe='minute',
                    aggregate=15,
                    days_limit=days_limit
                )
                
                if pool_data is not None and not pool_data.empty:
                    # 保存数据（不包含索引）
                    pool_data.to_csv(file_path, index=False)
                    print(f"已保存 {token_name} 的完整历史数据到: {filename}")
                    print(f"数据时间范围: {pool_data['timestamp'].min()} 到 {pool_data['timestamp'].max()}")
                    print(f"总数据条数: {len(pool_data)} 行")
                
                # 添加延时避免请求过快
                time.sleep(2)
                
            except Exception as e:
                print(f"处理行 {index} 时出错: {str(e)}")
                continue
        
        print("\n所有代币历史数据处理完成")
        return True
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        return False

def convert_to_utc8(df, timestamp_col='timestamp'):
    """
    将秒级时间戳转换为UTC+8时区的日期时间格式
    
    参数:
        df: pandas DataFrame
        timestamp_col: 时间列的列名
    返回:
        转换后的DataFrame
    """
    if timestamp_col in df.columns:
        # 将秒级时间戳转换为datetime对象（默认UTC）
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], unit='s', utc=True)
        # 转换为UTC+8时区
        df[timestamp_col] = df[timestamp_col].dt.tz_convert('Asia/Shanghai')
        # 移除时区信息，保持日期时间格式
        df[timestamp_col] = df[timestamp_col].dt.tz_localize(None)
    return df

if __name__ == "__main__":
    process_pools() 