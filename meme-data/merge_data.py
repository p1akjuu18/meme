import pandas as pd
import os

# 获取桌面路径
desktop_path = os.path.expanduser("~/Desktop")

# 读取所有文件
processed_data = pd.read_excel(os.path.join(desktop_path, "processed_data3.xlsx"))
chain_data = pd.read_excel(os.path.join(desktop_path, "chain.fm+extracted_data3.xlsx"))
expanded_data = pd.read_excel(os.path.join(desktop_path, "expanded_duplicates.xlsx"))

# 创建一个 Excel 写入器
output_file = os.path.join(desktop_path, "merged_data.xlsx")
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # 保存原始数据到不同的sheet
    processed_data.to_excel(writer, sheet_name='Processed Data', index=False)
    chain_data.to_excel(writer, sheet_name='Chain Data', index=False)
    expanded_data.to_excel(writer, sheet_name='Expanded Data', index=False)
    
    # 通过地址关联数据
    # 首先确认每个数据框中的地址列名
    print("Processed Data 列名:", processed_data.columns.tolist())
    print("Chain Data 列名:", chain_data.columns.tolist())
    print("Expanded Data 列名:", expanded_data.columns.tolist())
    
    # 合并数据（这里假设地址列名为'钱包地址'，如果不是请告诉我）
    merged_data = processed_data.merge(chain_data, 
                                     on='address', 
                                     how='outer',
                                     suffixes=('_processed', '_chain'))
    
    merged_data = merged_data.merge(expanded_data,
                                  on='address ',
                                  how='outer',
                                  suffixes=('', '_expanded'))
    
    # 保存合并后的数据
    merged_data.to_excel(writer, sheet_name='Merged Data', index=False)

print(f"数据已合并并保存到: {output_file}") 