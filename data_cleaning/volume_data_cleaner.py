import pandas as pd
import os
from datetime import datetime

def get_latest_coingecko_results():
    """获取最新的token_query_results文件"""
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"错误：未找到数据文件夹: {data_dir}")
        return None

    # 查找token_query_results_all_开头的文件
    result_files = [f for f in os.listdir(data_dir) if f.startswith('token_query_results_all_') and f.endswith('.xlsx')]
    if not result_files:
        print("错误：未找到token_query_results文件")
        return None

    # 按文件名排序（因为文件名包含时间戳）
    latest_file = sorted(result_files)[-1]
    return os.path.join(data_dir, latest_file)

def clean_token_data(file_path=None):
    """清洗代币数据"""
    try:
        # 如果没有提供文件路径，获取最新的文件
        if file_path is None:
            file_path = get_latest_coingecko_results()
            if not file_path:
                print("未找到可处理的文件")
                return None
        
        print(f"正在处理文件: {file_path}")
        
        # 读取文件
        df = pd.read_excel(file_path)
        print(f"原始数据量: {len(df)} 行")
        
        # 删除交易池_交易量_1小时为0或空的行
        df = df[df['交易池_交易量_1小时'] != 0]
        df = df.dropna(subset=['交易池_交易量_1小时'])
        
        # 删除交易池_交易次数_1小时_卖出小于30的行
        df = df[df['交易池_交易次数_1小时_卖出'] >= 30]
        
        # 删除24h成交量(USD)为0的行
        df = df[df['24h成交量(USD)'] >= 100000]
        
        # 删除完全稀释估值(USD)小于900000的行
        df = df[(df['完全稀释估值(USD)'] >= 900000)]
        
        # 处理代币地址列，去除solana_前缀
        df['代币地址'] = df['代币地址'].str.replace('solana_', '')
        
        # 生成输出文件名，使用统一的时间戳格式
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join('data', f'token_query_results_filtered_{timestamp}.xlsx')
        
        # 保存数据为Excel格式
        df.to_excel(output_file, index=False)
        
        print(f"\n清洗后的数据已保存至: {output_file}")
        print(f"清洗后数据量: {len(df)} 行")
        
        return output_file
        
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    clean_token_data() 