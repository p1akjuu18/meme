import pandas as pd
import numpy as np
import os
from datetime import datetime

def calculate_rsi(data, periods=14):
    """
    计算RSI指标
    """
    # 计算价格变化
    delta = data['close'].diff()
    
    # 分别获取上涨和下跌
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    
    # 计算平均上涨和下跌
    avg_gain = gain.rolling(window=periods).mean()
    avg_loss = loss.rolling(window=periods).mean()
    
    # 计算相对强度（RS）
    rs = avg_gain / avg_loss
    
    # 计算RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def process_token_files():
    # 获取桌面路径
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    token_folder = os.path.join(desktop_path, 'token')
    
    # 确保token文件夹存在
    if not os.path.exists(token_folder):
        print("Token文件夹不存在")
        return
    
    # 创建RSI结果文件夹
    rsi_folder = os.path.join(desktop_path, 'token_rsi')
    os.makedirs(rsi_folder, exist_ok=True)
    
    # 处理每个CSV文件
    for filename in os.listdir(token_folder):
        if filename.endswith('.csv'):
            try:
                print(f"\n处理文件: {filename}")
                
                # 读取CSV文件
                file_path = os.path.join(token_folder, filename)
                df = pd.read_csv(file_path)
                
                # 确保timestamp列是datetime类型
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                
                # 计算RSI
                df['rsi'] = calculate_rsi(df)
                
                # 生成新的文件名
                symbol = filename.split('.')[0]  # 移除.csv扩展名
                new_filename = f"{symbol}_RSI.csv"
                
                # 保存结果
                output_path = os.path.join(rsi_folder, new_filename)
                df.to_csv(output_path, index=False)
                
                print(f"已计算 {symbol} 的RSI")
                print(f"RSI范围: {df['rsi'].min():.2f} 到 {df['rsi'].max():.2f}")
                
                # 生成RSI警报
                latest_rsi = df['rsi'].iloc[-1]
                if latest_rsi < 30:
                    print(f"警报: {symbol} 可能超卖 (RSI = {latest_rsi:.2f})")
                elif latest_rsi > 70:
                    print(f"警报: {symbol} 可能超买 (RSI = {latest_rsi:.2f})")
                
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")
                continue

if __name__ == "__main__":
    process_token_files() 