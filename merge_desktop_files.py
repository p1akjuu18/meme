import pandas as pd
import os
import numpy as np
from datetime import datetime
import config  # 导入config模块

def merge_files():
    # 使用config中定义的DATA_DIR
    data_dir = config.DATA_DIR
    
    # 确保data目录存在
    if not os.path.exists(data_dir):
        print(f"错误：data目录不存在: {data_dir}")
        os.makedirs(data_dir)
        print(f"已创建data目录: {data_dir}")
        return None
    
    # 查找最新的文件
    token_dir = os.path.join(data_dir, 'token')  # 添加token子文件夹路径
    if not os.path.exists(token_dir):
        print(f"错误：token目录不存在: {token_dir}")
        os.makedirs(token_dir)
        print(f"已创建token目录: {token_dir}")
        return None

    price_analysis_files = [f for f in os.listdir(token_dir) if f.startswith('price_analysis_results') and f.endswith('.csv')]
    token_info_files = [f for f in os.listdir(data_dir) if f.startswith('token_info_basic') and f.endswith('.xlsx')]
    token_data_files = [f for f in os.listdir(data_dir) if f.startswith('token_data_sorted') and f.endswith('.xlsx')]
    
    # 检查每种文件是否存在
    missing_files = []
    if not price_analysis_files:
        missing_files.append("price_analysis_results_*.csv")
    if not token_info_files:
        missing_files.append("token_info_basic_*.xlsx")
    if not token_data_files:
        missing_files.append("token_data_sorted_*.xlsx")
    
    if missing_files:
        print("错误：以下文件未找到：")
        for file in missing_files:
            print(f"- {file}")
        print(f"\n当前data目录下的文件列表：")
        for file in os.listdir(data_dir):
            print(f"- {file}")
        return None
        
    # 获取最新的文件
    price_analysis_file = os.path.join(token_dir, sorted(price_analysis_files)[-1])
    token_info_file = os.path.join(data_dir, sorted(token_info_files)[-1])
    token_data_file = os.path.join(data_dir, sorted(token_data_files)[-1])
    
    print(f"\n将使用以下文件进行合并：")
    print(f"价格分析文件: {os.path.basename(price_analysis_file)}")
    print(f"代币信息文件: {os.path.basename(token_info_file)}")
    print(f"代币数据文件: {os.path.basename(token_data_file)}")
    
    try:
        # 分别读取文件
        price_df = pd.read_csv(price_analysis_file)
        token_df = pd.read_excel(token_info_file)
        token_data_df = pd.read_excel(token_data_file)
        
        # 对token_data_processed_final进行处理，只保留每个代币地址的第一条记录
        token_data_df = token_data_df.drop_duplicates(subset=['代币地址'], keep='first')
        
        # 将token列转换为小写以进行不区分大小写的匹配
        price_df['token'] = price_df['token'].str.lower()
        token_df['符号'] = token_df['符号'].str.lower()
        
        # 首先合并price_analysis和token_info
        merged_df = pd.merge(token_df, 
                            price_df,
                            left_on='符号',
                            right_on='token',
                            how='inner')
        
        # 删除重复的token列
        if 'token' in merged_df.columns:
            merged_df = merged_df.drop('token', axis=1)
        
        # 再合并token_data的信息
        final_df = pd.merge(merged_df,
                           token_data_df[['代币地址', '买入钱包数', '聪明钱包总余额', '代币存活天数']],
                           on='代币地址',
                           how='inner')
        
        # 计算ATH市值 = 完全稀释估值/当前价格*最高价
        final_df['ATH'] = (final_df['完全稀释估值(USD)'] / final_df['价格(USD)'] * final_df['max_price']).round(2)
        
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        output_file = os.path.join(data_dir, f"merged_token_info_analyzed_{timestamp}.xlsx")
        final_df.to_excel(output_file, index=False)
        print(f"文件已合并并保存至: {output_file}")
        
        # 打印匹配统计信息
        total_rows = len(final_df)
        print(f"\n匹配统计:")
        print(f"完全匹配的记录数: {total_rows}")
        
        # 打印一些关键指标的统计信息
        print("\n关键指标统计:")
        print("平均ATH:", round(final_df['ATH'].mean(), 2))
        print("最大ATH:", round(final_df['ATH'].max(), 2))
        print("最小ATH:", round(final_df['ATH'].min(), 2))
        
        return output_file
        
    except FileNotFoundError as e:
        print(f"错误：找不到文件 - {e}")
        return None
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        # 如果出错，显示更详细的信息
        if 'price_df' in locals():
            print("\nPrice Analysis 文件的前几行:")
            print(price_df.head())
        if 'token_df' in locals():
            print("\nToken Info 文件的前几行:")
            print(token_df.head())
        if 'token_data_df' in locals():
            print("\nToken Data 文件的前几行:")
            print(token_data_df.head())
        return None

if __name__ == "__main__":
    merge_files()