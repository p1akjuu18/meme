import pandas as pd
import os

def process_data_to_sheets():
    """处理数据并分配到不同的sheet"""
    try:
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        input_file = os.path.join(desktop_path, "processed_tokens_20241231.xlsx")
        
        if not os.path.exists(input_file):
            print(f"错误：未找到文件 {input_file}")
            return
        
        # 读取两个sheet的数据
        df_tokens = pd.read_excel(input_file, sheet_name='Token Data')
        df_names = pd.read_excel(input_file, sheet_name='Search Data')
        
        print(f"成功读取数据:")
        print(f"Token数据: {len(df_tokens)} 行")
        print(f"搜索数据: {len(df_names)} 行")
        
        # 清理数据
        df_tokens = df_tokens.dropna(subset=['Token Address', 'Token Name']).drop_duplicates()
        df_names = df_names.dropna(subset=['Token Name']).drop_duplicates()
        
        # 创建输出文件
        output_file = os.path.join(desktop_path, "final_tokens_20241231.xlsx")
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df_tokens.to_excel(writer, sheet_name='Token Addresses', index=False)
            df_names.to_excel(writer, sheet_name='Token Names', index=False)
        
        print("\n数据处理完成！")
        print(f"Token地址数量: {len(df_tokens)}")
        print(f"代币名称数量: {len(df_names)}")
        print(f"处理后的数据已保存至: {output_file}")
        
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")

if __name__ == "__main__":
    process_data_to_sheets() 