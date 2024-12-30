import pandas as pd
import os

# 获取桌面路径
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
file_path = os.path.join(desktop_path, "merged_token_info_analyzed.xlsx")

try:
    # 读取Excel文件
    df = pd.read_excel(file_path)
    
    # 打印列名
    print("\n=== Excel文件的列名 ===")
    for i, column in enumerate(df.columns, 1):
        print(f"{i}. {column}")
    
    # 打印前1行数据的预览
    print("\n=== 数据预览（第1行）===")
    pd.set_option('display.max_columns', None)  # 显示所有列
    pd.set_option('display.width', None)        # 不限制宽度
    pd.set_option('display.max_colwidth', None) # 不限制列宽
    print(df.iloc[0].to_string())
    
except FileNotFoundError:
    print(f"错误：找不到文件 {file_path}")
except Exception as e:
    print(f"读取文件时出错：{str(e)}") 