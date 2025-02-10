import os
import sys

# 添加项目根目录到 Python 路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(root_dir, '.env'))

import pandas as pd
from datetime import datetime, timedelta
import time
import requests
import numpy as np
import asyncio
from coingecko_client import CoinGeckoClient
from data_analysis.token.token_price_analysis import analyze_token_data
from merge_desktop_files import merge_files
import config  # Import the config module for path management

def convert_to_utc8(df, timestamp_col='timestamp'):
    """
    将DataFrame中的时间列从UTC+0转换为UTC+8
    
    参数:
        df: pandas DataFrame
        timestamp_col: 时间列的列名
    返回:
        转换后的DataFrame
    """
    if timestamp_col in df.columns:
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        # 如果数据没有时区信息，假定它是UTC+8
        if df[timestamp_col].dt.tz is None:
            df[timestamp_col] = df[timestamp_col].dt.tz_localize('Asia/Shanghai')
        # 如果数据有时区信息但不是UTC+8，转换为UTC+8
        else:
            df[timestamp_col] = df[timestamp_col].dt.tz_convert('Asia/Shanghai')
        # 保持时区信息
        return df
    return df

class TokenDataUpdater:
    def __init__(self):
        self.token_folder = config.TOKEN_FOLDER
        
        # 确保token文件夹存在
        if not os.path.exists(self.token_folder):
            os.makedirs(self.token_folder)
            print(f"创建token文件夹: {self.token_folder}")
        
        # 打印当前使用的路径
        print(f"使用token文件夹路径: {self.token_folder}")
        
        # 从环境变量获取API密钥
        api_key = os.getenv('COINGECKO_API_KEY', '')
        if not api_key:
            raise ValueError("未设置COINGECKO_API_KEY环境变量")
            
        self.client = CoinGeckoClient(api_key=api_key)

    def get_latest_data(self, pool_address):
        """
        获取最新的15分钟K线数据
        """
        try:
            # 获取多条数据，而不是只获取一条
            data = self.client.get_pool_ohlcv(
                network='solana',
                pool_address=pool_address,
                timeframe='minute',
                aggregate=15,
                limit=10  # 获取最近10条数据
            )
            if data is not None and not data.empty:
                # 将UTC+0时间转换为UTC+8
                data['timestamp'] = pd.to_datetime(data['timestamp']).dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai').dt.tz_localize(None)
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
                # CSV文件中的时间已经是UTC+8，直接转换为datetime
                existing_data['timestamp'] = pd.to_datetime(existing_data['timestamp'])
                
                # 获取最后一条数据的时间
                last_timestamp = existing_data['timestamp'].max()
                
                # 筛选出新的数据点（此时两者都是UTC+8时间）
                new_records = new_data[new_data['timestamp'] > last_timestamp]
                
                if not new_records.empty:
                    # 合并数据
                    updated_data = pd.concat([existing_data, new_records])
                    # 去重并按时间排序
                    updated_data = updated_data.drop_duplicates(subset='timestamp').sort_values('timestamp')
                    # 保存更新后的数据
                    updated_data.to_csv(file_path, index=False)
                    print(f"{symbol}: 更新了 {len(new_records)} 条数据")
                    return True
                else:
                    print(f"{symbol}: 无更新")
                    return False
            else:
                # 如果文件不存在，直接保存新数据
                new_data.to_csv(file_path, index=False)
                print(f"{symbol}: 创建文件，{len(new_data)} 条数据")
                return True
                
        except Exception as e:
            print(f"{symbol}: 更新失败 - {str(e)}")
            return False

    def run_updates(self):
        """
        持续运行更新程序
        """
        print("开始实时数据更新...")
        
        # 查找最新的token_data_sorted文件
        data_dir = config.DATA_DIR
        filtered_files = [f for f in os.listdir(data_dir) if f.startswith('token_data_sorted_')]
        if not filtered_files:
            print("未找到token数据文件")
            return
            
        # 按文件名排序，获取最新的文件
        latest_file = sorted(filtered_files)[-1]
        query_results_path = os.path.join(data_dir, latest_file)
        print(f"使用最新的数据文件: {latest_file}")
        
        try:
            tokens_df = pd.read_excel(query_results_path)
        except Exception as e:
            print(f"读取token查询结果文件出错: {str(e)}")
            return
            
        while True:
            update_count = 0
            try:
                for _, row in tokens_df.iterrows():
                    if pd.isna(row['币种']) or pd.isna(row['交易池_地址']):
                        continue
                        
                    if self.update_token_file(row['币种'], row['交易池_地址']):
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

    async def run_updates_async(self):
        """
        异步运行更新程序
        """
        print("开始异步实时数据更新...")
        
        # 查找最新的token_query_results文件
        data_dir = config.DATA_DIR
        filtered_files = [f for f in os.listdir(data_dir) if f.startswith('token_data_sorted_')]
        if not filtered_files:
            print("未找到token数据文件")
            return
            
        # 按文件名排序，获取最新的文件
        latest_file = sorted(filtered_files)[-1]
        query_results_path = os.path.join(data_dir, latest_file)
        print(f"使用最新的数据文件: {latest_file}")
        
        try:
            tokens_df = pd.read_excel(query_results_path)
        except Exception as e:
            print(f"读取token查询结果文件出错: {str(e)}")
            return
            
        while True:
            update_count = 0
            try:
                for _, row in tokens_df.iterrows():
                    if pd.isna(row['币种']) or pd.isna(row['交易池_地址']):
                        continue
                        
                    if self.update_token_file(row['币种'], row['交易池_地址']):
                        update_count += 1
                
                print(f"\n{datetime.now()}: 完成一轮更新，更新了 {update_count} 个代币的数据")
                
                # 在每次更新完成后运行价格分析
                if update_count > 0:
                    self.run_price_analysis()
                
                # 等待到下一个15分钟
                next_update = self.get_next_update_time()
                wait_seconds = (next_update - datetime.now()).total_seconds()
                if wait_seconds > 0:
                    print(f"等待 {wait_seconds:.0f} 秒后进行下一次更新...")
                    await asyncio.sleep(wait_seconds)
                    
            except Exception as e:
                print(f"更新过程出错: {str(e)}")
                await asyncio.sleep(60)  # 出错后等待1分钟再试

    def get_next_update_time(self):
        """
        计算下一个15分钟的更新时间
        """
        now = datetime.now()
        minutes = now.minute
        next_minutes = ((minutes // 15) + 1) * 15
        next_update = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=next_minutes)
        return next_update

    def run_price_analysis(self):
        """运行价格分析"""
        try:
            print("开始运行价格分析...")
            results = analyze_token_data(self.token_folder)
            if not results.empty:
                # 保存结果到CSV
                output_path = os.path.join(self.token_folder, "price_analysis_results.csv")
                results.to_csv(output_path, index=False)
                print(f"价格分析完成，结果已保存到: {output_path}")
                
                # 打印一些关键统计信息
                print("\n=== 价格分析统计 ===")
                print(f"分析的代币数量: {len(results)}")
                print(f"最大回调范围: {results['max_drawdown_percentage'].min():.2f}% - {results['max_drawdown_percentage'].max():.2f}%")
                print(f"平均回调: {results['max_drawdown_percentage'].mean():.2f}%")
                
                # 调用merge_files进行文件合并
                try:
                    merged_file = merge_files()
                    if merged_file:
                        print(f"文件合并完成，结果保存在: {merged_file}")
                    else:
                        print("文件合并失败")
                except Exception as e:
                    print(f"合并文件时出错: {str(e)}")
            else:
                print("价格分析未产生结果")
        except Exception as e:
            print(f"运行价格分析时出错: {str(e)}")

if __name__ == "__main__":
    updater = TokenDataUpdater()
    if len(sys.argv) > 1 and sys.argv[1] == "--async":
        asyncio.run(updater.run_updates_async())
    else:
        updater.run_updates()                       