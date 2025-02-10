import pandas as pd
import os

# 读取Excel文件
df = pd.read_excel('merge_owner_20241229.xlsx')

# 使用UTF-8编码保存为CSV
df.to_csv('merge_owner_20241229.csv', index=False, encoding='utf-8') 