import pandas as pd
import os

def merge_token_addresses():
    # 读取桌面上的文件
    desktop_path = os.path.expanduser("~/Desktop")
    
    # 读取第一个文件（包含代币地址的文件）
    file1_path = os.path.join(desktop_path, "token_query_results_all_20250108_205910_cleaned.xlsx")
    df1 = pd.read_excel(file1_path)
    
    # 读取第二个文件（需要添加地址的文件）
    file2_path = os.path.join(desktop_path, "clear_html_table_data_20250108_2037.xlsx")
    df2 = pd.read_excel(file2_path)
    
    # 创建符号到地址的映射字典（忽略大小写）
    symbol_to_address = dict(zip(df1['符号'].str.lower(), df1['代币地址']))
    
    # 获取所有列名
    columns = df2.columns.tolist()
    
    # 创建代币地址列
    token_addresses = df2['币种'].str.lower().map(symbol_to_address)
    
    # 重新组织DataFrame，将代币地址插入到第二列
    df2_new = pd.DataFrame()
    df2_new[columns[0]] = df2[columns[0]]  # 第一列
    df2_new['代币地址'] = token_addresses    # 插入代币地址作为第二列
    for col in columns[1:]:                # 添加剩余列
        df2_new[col] = df2[col]
    
    # 保存结果
    output_path = os.path.join(desktop_path, "merged_token_data_2025010888.xlsx")
    df2_new.to_excel(output_path, index=False)
    
    # 打印匹配统计信息
    total_rows = len(df2)
    matched_rows = token_addresses.notna().sum()
    print(f"\n匹配统计：")
    print(f"总行数: {total_rows}")
    print(f"成功匹配: {matched_rows}")
    print(f"匹配率: {(matched_rows/total_rows*100):.2f}%")
    print(f"\n处理完成，结果已保存至: {output_path}")

if __name__ == "__main__":
    merge_token_addresses() 