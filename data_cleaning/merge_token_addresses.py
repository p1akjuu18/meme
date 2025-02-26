import pandas as pd
import os
import glob
from datetime import datetime

def get_latest_file(directory, prefix):
    """获取指定目录下特定前缀的最新文件"""
    pattern = os.path.join(directory, f"{prefix}*.xlsx")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"未找到前缀为 {prefix} 的文件")
    return max(files, key=os.path.getctime)

def merge_token_addresses(data_dir="data"):
    try:
        # 获取最新的文件
        token_query_file = get_latest_file(data_dir, "token_query_results_filtered_")
        clear_html_file = get_latest_file(data_dir, "clear_html_table_data_")
        
        # 读取第一个文件（包含代币地址的文件）
        df1 = pd.read_excel(token_query_file)
        
        # 读取第二个文件（需要添加地址的文件）
        df2 = pd.read_excel(clear_html_file)
        
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
        
        # 生成输出文件名
        output_filename = f"merged_token_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        output_path = os.path.join(data_dir, output_filename)
        df2_new.to_excel(output_path, index=False)
        
        # 打印匹配统计信息
        total_rows = len(df2)
        matched_rows = token_addresses.notna().sum()
        print(f"\n匹配统计：")
        print(f"总行数: {total_rows}")
        print(f"成功匹配: {matched_rows}")
        print(f"匹配率: {(matched_rows/total_rows*100):.2f}%")
        print(f"\n处理完成，结果已保存至: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"处理过程中出现错误：{str(e)}")
        raise

if __name__ == "__main__":
    merge_token_addresses() 