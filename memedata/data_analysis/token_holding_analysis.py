import pandas as pd
import os

def analyze_token_holdings():
    # 读取合并后的文件
    desktop_path = os.path.expanduser("~/Desktop")
    file_path = os.path.join(desktop_path, "merged_token_data_2025010888.xlsx")
    df = pd.read_excel(file_path)
    
    # 计算每个代币地址的钱包数量
    wallet_counts = df.groupby('代币地址')['钱包地址'].count().reset_index()
    wallet_counts = wallet_counts.rename(columns={'钱包地址': '买入钱包数'})
    
    # 将钱包数量信息合并回原始数据
    df = pd.merge(df, wallet_counts, on='代币地址', how='left')
    
    # 按代币地址和买入钱包数排序
    df_sorted = df.sort_values(['买入钱包数', '代币地址'], ascending=[False, True])
    
    # 保存结果
    output_path = os.path.join(desktop_path, "token_data_sorted_202501088.xlsx")
    df_sorted.to_excel(output_path, index=False)
    
    print(f"\n结果已保存至: {output_path}")
    print(f"总计整理了 {len(wallet_counts)} 个不同的代币地址")

if __name__ == "__main__":
    analyze_token_holdings() 