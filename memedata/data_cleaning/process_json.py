import pandas as pd
import json
import os

# 获取用户桌面路径
desktop_path = os.path.expanduser("~/Desktop")

# 直接从桌面读取JSON文件
file_path = os.path.join(desktop_path, "raw_json_data_20250104_1727.json")
output_path = file_path.replace('.json', '.xlsx')

# 检查文件是否存在
if not os.path.exists(file_path):
    print(f"错误：找不到文件 {file_path}")
    exit(1)

# 读取JSON数据
with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# 提取地址和代币信息
extracted_data = []
for address, details in data.items():
    tokens = details.get("props", {}).get("pageProps", {}).get("tokens", [])
    for token in tokens:
        row = {
            'Token Address': token.get('address'),
            'Token Name': token.get('name')
        }
        extracted_data.append(row)

# 转换为DataFrame
df = pd.DataFrame(extracted_data)

# 去除重复数据
df = df.drop_duplicates()

# 保存到Excel
df.to_excel(output_path, index=False)

print(f"数据已成功保存到: {output_path}") 