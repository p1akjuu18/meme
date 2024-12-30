import pandas as pd
import os
import numpy as np

# 获取桌面路径
desktop = os.path.join(os.path.expanduser("~"), "Desktop")

# 读取三个文件
price_analysis_file = os.path.join(desktop, "price_analysis_results.csv")
token_info_file = os.path.join(desktop, "token_info_updated.xlsx")
token_data_file = os.path.join(desktop, "token_data_processed_final.xlsx")

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
                        how='left')
    
    # 删除重复的token列
    if 'token' in merged_df.columns:
        merged_df = merged_df.drop('token', axis=1)
    
    # 再合并token_data的信息
    final_df = pd.merge(merged_df,
                       token_data_df[['代币地址', '买入钱包数', '聪明钱包总余额']],
                       on='代币地址',
                       how='left')
    
    # 计算ATH市值 = 完全稀释估值/当前价格*最高价
    final_df['ATH'] = (final_df['完全稀释估值(USD)'] / final_df['价格(USD)'] * final_df['max_price']).round(2)
    
    # 将结果保存到新的Excel文件
    output_file = os.path.join(desktop, "merged_token_info_analyzed.xlsx")
    final_df.to_excel(output_file, index=False)
    print(f"文件已合并并保存至: {output_file}")
    
    # 打印匹配统计信息
    total_rows = len(token_df)
    matched_rows = final_df['max_price'].notna().sum()
    smart_money_matched = final_df['买入钱包数'].notna().sum()
    print(f"\n匹配统计:")
    print(f"总行数: {total_rows}")
    print(f"价格分析匹配行数: {matched_rows}")
    print(f"聪明钱包数据匹配行数: {smart_money_matched}")
    print(f"价格分析匹配率: {(matched_rows/total_rows*100):.2f}%")
    print(f"聪明钱包数据匹配率: {(smart_money_matched/total_rows*100):.2f}%")
    
    # 打印一些关键指标的统计信息
    print("\n关键指标统计:")
    print("平均ATH:", final_df['ATH'].mean().round(2))
    print("最大ATH:", final_df['ATH'].max().round(2))
    print("最小ATH:", final_df['ATH'].min().round(2))
    
except FileNotFoundError as e:
    print(f"错误：找不到文件 - {e}")
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