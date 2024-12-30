import pandas as pd
import os
from datetime import datetime, timedelta

def analyze_token_data(folder_path):
    results = []
    
    # 检查并打印文件夹内容
    print(f"\n正在检查文件夹: {folder_path}")
    try:
        files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        print(f"找到的CSV文件数量: {len(files)}")
    except Exception as e:
        print(f"读取文件夹出错: {str(e)}")
        return pd.DataFrame()
    
    # 遍历文件夹中的所有文件
    processed_count = 0
    error_count = 0
    
    for filename in files:
        file_path = os.path.join(folder_path, filename)
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 确保有必要的列
            required_columns = ['timestamp', 'high', 'close', 'low']
            if all(col in df.columns for col in required_columns):
                # 转换timestamp为datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # 获取开始时间后15分钟的时间点
                start_time = df['timestamp'].min()
                cutoff_time = start_time + timedelta(minutes=15)
                
                # 过滤掉前15分钟的数据
                df_filtered = df[df['timestamp'] > cutoff_time].copy()
                
                if len(df_filtered) > 0:
                    # 找到最高价和对应时间
                    max_price = df_filtered['high'].max()
                    max_price_idx = df_filtered['high'].idxmax()
                    max_price_time = df_filtered.loc[max_price_idx, 'timestamp']
                    
                    # 只看最高价之后的数据来计算回调
                    df_after_high = df_filtered.loc[max_price_idx:].copy()
                    
                    if len(df_after_high) > 1:  # 确保最高价后还有数据
                        lowest_after_high = df_after_high['low'].min()
                        max_drawdown = (max_price - lowest_after_high) / max_price * 100
                        lowest_time = df_after_high.loc[df_after_high['low'].idxmin(), 'timestamp']
                    else:
                        max_drawdown = 0
                        lowest_time = max_price_time
                    
                    # 存储结果
                    token_name = filename.replace('.csv', '')
                    results.append({
                        'token': token_name,
                        'max_price': max_price,
                        'max_price_time': max_price_time,
                        'lowest_after_high': lowest_after_high if len(df_after_high) > 1 else max_price,
                        'lowest_time': lowest_time,
                        'max_drawdown_percentage': max_drawdown,
                        'analysis_start_time': cutoff_time,
                        'initial_price': df_filtered['close'].iloc[0],
                        'final_price': df_filtered['close'].iloc[-1],
                        'data_points': len(df_filtered)
                    })
                    processed_count += 1
                else:
                    print(f"警告: {filename} 过滤后没有足够的数据")
                    error_count += 1
            else:
                print(f"警告: 文件 {filename} 格式不正确")
                error_count += 1
            
        except Exception as e:
            print(f"处理文件 {filename} 时出错: {str(e)}")
            error_count += 1
    
    print(f"\n成功处理的文件数量: {processed_count}")
    print(f"处理失败的文件数量: {error_count}")
    
    # 转换结果为DataFrame并按最大回调排序
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df = results_df.sort_values('max_drawdown_percentage', ascending=False)
    return results_df

def main():
    # 设置数据文件夹路径
    desktop_path = os.path.expanduser("~/Desktop")
    folder_path = os.path.join(desktop_path, "token0108")
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误：找不到文件夹 {folder_path}")
        return
    
    # 分析数据
    results = analyze_token_data(folder_path)
    
    # 格式化输出
    if not results.empty:
        print("\n=== 代币价格分析结果 ===")
        print("(忽略首次上线后15分钟内数据)")
        print("\n按最大回调比例排序:")
        for _, row in results.iterrows():
            print(f"\n代币: {row['token']}")
            print(f"分析开始时间: {row['analysis_start_time']}")
            print(f"数据点数量: {row['data_points']}")
            print(f"初始价格: {row['initial_price']:.8f}")
            print(f"最高价: {row['max_price']:.8f}")
            print(f"最高价时间: {row['max_price_time']}")
            print(f"最高价后最低价: {row['lowest_after_high']:.8f}")
            print(f"最低价时间: {row['lowest_time']}")
            print(f"最终价格: {row['final_price']:.8f}")
            print(f"最大回调: {row['max_drawdown_percentage']:.2f}%")
        
        # 保存结果到CSV
        output_path = os.path.join(folder_path, "price_analysis_results.csv")
        results.to_csv(output_path, index=False)
        print(f"\n分析结果已保存到: {output_path}")
    else:
        print("没有找到可分析的数据")

if __name__ == "__main__":
    main() 