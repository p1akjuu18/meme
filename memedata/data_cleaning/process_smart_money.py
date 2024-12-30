import pandas as pd
from collections import defaultdict

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    处理数据的核心逻辑
    """
    # 确保DataFrame不为空且有数据
    if df.empty or len(df.columns) == 0:
        return pd.DataFrame({'label': [], 'address': []})
    
    # 1. 创建新的DataFrame来存储处理后的数据
    new_rows = []
    
    # 2. 遍历原始数据
    for i in range(0, len(df)):
        try:
            # 安全地获取单元格值
            cell_value = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ""
            
            # 如果这一行包含地址（通常较长的字符串）
            if len(cell_value) > 30:  # 假设地址字符串长度大于30
                # 清理地址（去掉前15个字符）
                address = clean_first_column(cell_value)
                # 将地址移到上一行的第二列
                if new_rows:  # 确保有上一行
                    new_rows[-1][1] = address
            else:
                # 这是标签行，创建新行
                new_rows.append([cell_value, None])
        except Exception as e:
            print(f"处理第 {i} 行时出错: {str(e)}")
            continue
    
    # 3. 创建新的DataFrame
    result_df = pd.DataFrame(new_rows, columns=['label', 'address'])
    
    # 4. 删除没有地址的行（但保留第一行）
    if len(result_df) > 0:
        first_row = result_df.iloc[0:1]  # 保存第一行
        other_rows = result_df.iloc[1:]  # 其他行
        other_rows = other_rows.dropna(subset=['address'])  # 对其他行进行过滤
        result_df = pd.concat([first_row, other_rows])  # 重新组合
    
    # 确保结果不为空
    if result_df.empty:
        result_df = pd.DataFrame({'label': ['空数据'], 'address': ['']})
    
    return result_df

def clean_first_column(text: str) -> str:
    """
    清理第一列中的重复部分
    去除前面的 "6个字母 + ... + 6个字母"（共15个字符）
    """
    if not isinstance(text, str):
        return text
    return text[15:]

def merge_all_sheets(input_path: str, output_path: str) -> None:
    """
    合并所有sheet的数据，保留所有数据行（包括重复的）
    """
    # 存储所有数据
    all_data = []
    
    # 读取所有sheet的数据
    excel_file = pd.ExcelFile(input_path)
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(input_path, sheet_name=sheet_name)
        # 只保留label和address列
        df = df[['label', 'address']]
        # 添加sheet来源信息
        df['sheet'] = sheet_name
        all_data.append(df)
    
    # 合并所有数据
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"合并后总数据行数: {len(combined_df)}")
    
    # 创建结果DataFrame
    result_df = combined_df.copy()
    
    # 为每行添加基本的label_1
    result_df['label_1'] = result_df.apply(lambda x: f"{x['label']}({x['sheet']})", axis=1)
    
    # 找出重复的地址
    duplicated_addresses = result_df[result_df.duplicated(subset=['address'], keep=False)]['address'].unique()
    
    # 对重复地址进行处理
    for addr in duplicated_addresses:
        # 获取该地址的所有记录
        addr_records = result_df[result_df['address'] == addr].copy()
        # 为这个地址的所有记录创建额外的label列
        for i, (_, record) in enumerate(addr_records.iterrows(), 1):
            col_name = f'label_{i}'
            if col_name not in result_df.columns:
                result_df[col_name] = None
            # 更新所有具有相同地址的行
            result_df.loc[result_df['address'] == addr, col_name] = f"{record['label']}({record['sheet']})"
    
    # 删除原始的label和sheet列
    result_df = result_df.drop(['label', 'sheet'], axis=1)
    
    print(f"最终数据行数: {len(result_df)}")
    
    # 保存结果
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        result_df.to_excel(writer, sheet_name='owner', index=False)
    
    print(f'数据处理完成，文件已保存至: {output_path}')

if __name__ == "__main__":
    INPUT_PATH = 'C:/Users/Admin/Desktop/masonaddress.xlsx'
    OUTPUT_PATH = 'C:/Users/Admin/Desktop/masonaddress_processed.xlsx'
    
    # 处理原始Excel文件
    excel_file = pd.ExcelFile(INPUT_PATH)
    with pd.ExcelWriter(OUTPUT_PATH, engine='openpyxl') as writer:
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(INPUT_PATH, sheet_name=sheet_name)
            df = process_data(df)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f'原始处理完成，文件已保存至: {OUTPUT_PATH}')
    
    # 合并所有sheet的地址
    MERGED_OUTPUT_PATH = 'C:/Users/Admin/Desktop/masonaddress_merged.xlsx'
    merge_all_sheets(OUTPUT_PATH, MERGED_OUTPUT_PATH) 