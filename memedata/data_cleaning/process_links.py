import pandas as pd
import os
import urllib.parse
from datetime import datetime

def process_links_data():
    """处理链接数据文件"""
    try:
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        links_file = os.path.join(desktop_path, "raw_links_data_20250108_1652.xlsx")
        
        if not os.path.exists(links_file):
            print(f"错误：未找到链接文件 {links_file}")
            return
        
        # 处理链接数据
        df_links = pd.read_excel(links_file)
        print(f"成功读取链接数据，共 {len(df_links)} 行")
        
        # 按3行一组处理链接数据
        processed_links = {
            'Token Address': [],
            'Token Name': []
        }
        
        for i in range(0, len(df_links), 3):
            group = df_links.iloc[i:i+3]
            if len(group) == 3:
                if (group.iloc[0]['Link URL'] == group.iloc[1]['Link URL'] and 
                    group.iloc[0]['Link URL'] != group.iloc[2]['Link URL']):
                    token_address = group.iloc[0]['Link URL'].split('token/')[-1]
                    token_name = group.iloc[2]['Link URL'].split('search?q=$')[-1]
                    token_name = urllib.parse.unquote(token_name)
                    
                    processed_links['Token Address'].append(token_address)
                    processed_links['Token Name'].append(token_name)
        
        # 创建DataFrame并保存结果
        df_result = pd.DataFrame(processed_links)
        
        # 去除重复数据
        df_result = df_result.drop_duplicates()
        
        # 保存处理后的数据（添加时间戳）
        current_time = datetime.now().strftime("%Y%m%d_%H%M")
        output_file = os.path.join(desktop_path, f"processed_links_{current_time}.xlsx")
        df_result.to_excel(output_file, index=False)
        
        print("\n数据处理完成！")
        print(f"处理结果: {len(df_result)} 行")
        print(f"数据已保存至: {output_file}")
        
        # 显示前几行数据作为示例
        print("\n数据示例:")
        print(df_result.head())
        
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def read_processed_links():
    """读取并显示处理后的链接文件内容"""
    try:
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        processed_file = os.path.join(desktop_path, "processed_links.xlsx")
        
        if not os.path.exists(processed_file):
            print(f"错误：未找到文件 {processed_file}")
            return
            
        # 读取Excel文件
        df = pd.read_excel(processed_file)
        
        print(f"\n成功读取文件，共 {len(df)} 行数据")
        print("\n数据预览:")
        print(df.head())
        
        return df
        
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_links_data()  # 如果需要处理数据，取消注释此行
 