from pycoingecko import CoinGeckoAPI
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
import mplfinance as mpf
import matplotlib.pyplot as plt

class HistoricalDataFetcher:
    def __init__(self):
        self.cg = CoinGeckoAPI(api_key="CG-W6NCZupELQfrh1irod8sb3cb")
        
    def get_historical_market_data(self, coin_id, vs_currency='usd', days='max', interval='daily'):
        """
        获取代币的历史价格数据
        
        参数:
            coin_id (str): CoinGecko上的代币ID
            vs_currency (str): 计价货币 (默认: 'usd')
            days (str/int): 获取多少天的数据 (默认: 'max')
            interval (str): 数据间隔 ('daily' 或 'hourly')
            
        返回:
            pandas.DataFrame: 包含时间戳、价格、交易量等数据的DataFrame
        """
        try:
            # 添加重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    market_data = self.cg.get_coin_market_chart_by_id(
                        id=coin_id,
                        vs_currency=vs_currency,
                        days=days,
                        interval=interval
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(1)  # 等待1秒后重试
            
            # 处理数据
            prices = market_data['prices']
            volumes = market_data['total_volumes']
            market_caps = market_data['market_caps']
            
            # 创建DataFrame
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['volume'] = [v[1] for v in volumes]
            df['market_cap'] = [m[1] for m in market_caps]
            
            # 转换时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        
        except Exception as e:
            print(f"获取历史数据时出错: {str(e)}")
            return None

    def save_to_csv(self, df, coin_id, output_path=None):
        """
        将数据保存为CSV文件
        
        参数:
            df (pandas.DataFrame): 要保存的数据
            coin_id (str): 代币ID
            output_path (str): 输出路径 (可选)
        """
        if df is not None:
            if output_path is None:
                output_path = f"{coin_id}_historical_data.csv"
            df.to_csv(output_path, index=False)
            print(f"数据已保存到: {output_path}")

    def get_pool_ohlcv(self, network, pool_address, timeframe='minute', aggregate=15):
        """
        获取代币池的OHLCV数据
        """
        try:
            # 使用正确的API调用方式
            headers = {
                'x-cg-pro-api-key': "CG-W6NCZupELQfrh1irod8sb3cb"
            }
            
            # 构建API URL
            base_url = "https://pro-api.coingecko.com/api/v3"
            # 修改URL构建方式，将aggregate作为查询参数
            endpoint = f"{base_url}/onchain/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}?aggregate={aggregate}"
            
            print(f"请求URL: {endpoint}")  # 添加调试信息
            
            # 使用requests库直接发送请求
            response = requests.get(endpoint, headers=headers)
            print(f"响应状态码: {response.status_code}")  # 添加调试信息
            
            response.raise_for_status()  # 检查响应状态
            data = response.json()
            
            if 'ohlcv_list' not in data:
                print(f"API响应: {data}")  # 添加调试信息
                raise Exception("未找到OHLCV数据")
            
            # 处理返回的数据
            ohlcv_data = data['ohlcv_list']
            
            # 创建DataFrame
            df = pd.DataFrame(ohlcv_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ])
            
            # 转换时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            return df
            
        except Exception as e:
            print(f"获取池OHLCV数据时出错: {str(e)}")
            if isinstance(e, requests.exceptions.HTTPError):
                print(f"API错误响应: {e.response.text}")  # 添加错误响应详情
            return None

    def save_ohlcv_to_csv(self, df, pool_address, timeframe, output_path=None):
        """
        将OHLCV数据保存为CSV文件
        
        参数:
            df (pandas.DataFrame): 要保存的数据
            pool_address (str): 代币池地址
            timeframe (str): 时间周期
            output_path (str): 输出路径 (可选)
        """
        if df is not None:
            if output_path is None:
                output_path = f"{pool_address}_{timeframe}_ohlcv.csv"
            df.to_csv(output_path, index=False)
            print(f"OHLCV数据已保存到: {output_path}")

    def plot_ohlcv(self, df, title=None, output_file=None):
        """
        绘制K线图
        
        参数:
            df (pandas.DataFrame): OHLCV数据
            title (str): 图表标题
            output_file (str): 输出文件路径
        """
        try:
            # 检查数据是否为空
            if df is None or df.empty:
                print("没有数据可以绘制")
                return
            
            print("数据预览:")
            print(df.head())
            print("\n数据列:", df.columns.tolist())
            
            # 设置时间索引
            df = df.set_index('timestamp')
            
            # 确保数据类型正确
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            print("\n处理后的数据预览:")
            print(df.head())
            print("\n数据类型:")
            print(df.dtypes)
            
            # 设置绘图样式
            style = mpf.make_mpf_style(
                base_mpf_style='yahoo',
                gridstyle='',  
                y_on_right=True,
                volume_alpha=0.5,
                rc={'figure.facecolor': 'white'}
            )
            
            # 绘制K线图
            fig, axes = mpf.plot(
                df,
                type='candle',
                volume=True,
                title=title,
                style=style,
                returnfig=True,
                figsize=(15, 10),
                panel_ratios=(3, 1),
                datetime_format='%Y-%m-%d %H:%M'
            )
            
            # 保存图片
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                print(f"K线图已保存到: {output_file}")
            
            # 显示图片
            plt.show()
            
        except Exception as e:
            print(f"绘制K线图时出错: {str(e)}")
            import traceback
            print("详细错误信息:")
            print(traceback.format_exc())

def main():
    fetcher = HistoricalDataFetcher()
    
    # 获取15分钟K线数据
    pool_data = fetcher.get_pool_ohlcv(
        network='solana',
        pool_address='J3b6dvheS2Y1cbMtVz5TCWXNegSjJDbUKxdUVDPoqmS7',
        timeframe='minute',
        aggregate=15
    )
    
    if pool_data is not None:
        print("获取到的15分钟OHLCV数据示例:")
        print(pool_data.head())
        
        # 保存数据到CSV
        fetcher.save_ohlcv_to_csv(pool_data, 'J3b6dvheS2Y1cbMtVz5TCWXNegSjJDbUKxdUVDPoqmS7', '15min')
        
        # 绘制并保存K线图
        title = 'Solana Token 15min OHLCV Chart'
        output_file = 'solana_token_15min_chart.png'
        fetcher.plot_ohlcv(pool_data, title=title, output_file=output_file)

if __name__ == "__main__":
    main() 