import pandas as pd
import os
from datetime import datetime, timedelta
import time
import requests
import numpy as np
from coingecko_client import CoinGeckoClient

class TokenDataUpdater:
    def __init__(self):
        self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        self.token_folder = os.path.join(self.desktop_path, 'token')
        self.client = CoinGeckoClient(api_key="CG-dJ6UcnVr8yvqw5Cvm8CywKvD")
        
    def get_latest_data(self, pool_address):
        """
        获取最新的15分钟K线数据
        """
        try:
            data = self.client.get_pool_ohlcv(
                network='solana',
                pool_address=pool_address,
                timeframe='minute',
                aggregate=15,
                limit=1
            )
            if data is not None and not data.empty:
                return data
        except Exception as e:
            print(f"获取最新数据出错: {str(e)}")
        return None

    def update_token_file(self, symbol, pool_address):
        """
        更新单个代币的数据文件
        """
        file_path = os.path.join(self.token_folder, f"{symbol}.csv")
        
        try:
            # 获取最新数据
            new_data = self.get_latest_data(pool_address)
            if new_data is None:
                return False
                
            # 如果文件存在，读取并更新
            if os.path.exists(file_path):
                existing_data = pd.read_csv(file_path)
                existing_data['timestamp'] = pd.to_datetime(existing_data['timestamp'])
                
                # 获取最后一条数据的时间
                last_timestamp = existing_data['timestamp'].max()
                
                # 只添加新的数据
                new_data = new_data[new_data['timestamp'] > last_timestamp]
                
                if not new_data.empty:
                    # 合并数据
                    updated_data = pd.concat([existing_data, new_data])
                    # 去重并按时间排序
                    updated_data = updated_data.drop_duplicates(subset='timestamp').sort_values('timestamp')
                    # 保存更新后的数据
                    updated_data.to_csv(file_path, index=False)
                    print(f"{symbol}: 添加了 {len(new_data)} 条新数据")
                    return True
                else:
                    print(f"{symbol}: 没有新数据")
                    return False
            else:
                # 如果文件不存在，直接保存新数据
                new_data.to_csv(file_path, index=False)
                print(f"{symbol}: 创建了新文件")
                return True
                
        except Exception as e:
            print(f"更新 {symbol} 数据时出错: {str(e)}")
            return False

    def run_updates(self):
        """
        持续运行更新程序
        """
        print("开始实时数据更新...")
        
        # 读取token_query_results文件获取代币列表
        query_results_path = os.path.join(self.desktop_path, 'token_query_results_all_20250108_205910_cleaned.xlsx')
        if not os.path.exists(query_results_path):
            print("找不到token查询结果文件")
            return
            
        tokens_df = pd.read_excel(query_results_path)
        
        while True:
            update_count = 0
            try:
                for _, row in tokens_df.iterrows():
                    if pd.isna(row['交易池_地址']) or pd.isna(row['符号']):
                        continue
                        
                    if self.update_token_file(row['符号'], row['交易池_地址']):
                        update_count += 1
                
                print(f"\n{datetime.now()}: 完成一轮更新，更新了 {update_count} 个代币的数据")
                
                # 等待到下一个15分钟
                next_update = self.get_next_update_time()
                wait_seconds = (next_update - datetime.now()).total_seconds()
                if wait_seconds > 0:
                    print(f"等待 {wait_seconds:.0f} 秒后进行下一次更新...")
                    time.sleep(wait_seconds)
                    
            except Exception as e:
                print(f"更新过程出错: {str(e)}")
                time.sleep(60)  # 出错后等待1分钟再试
                
    def get_next_update_time(self):
        """
        计算下一个15分钟的更新时间
        """
        now = datetime.now()
        minutes = now.minute
        next_minutes = ((minutes // 15) + 1) * 15
        next_update = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=next_minutes)
        return next_update

if __name__ == "__main__":
    updater = TokenDataUpdater()
    updater.run_updates() 