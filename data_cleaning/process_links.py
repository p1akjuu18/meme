import pandas as pd
import os
import urllib.parse
from datetime import datetime

def process_links_data():
    """处理链接数据文件"""
    try:
        # 使用data目录
        data_dir = "data"
        if not os.path.exists(data_dir):
            print(f"错误：未找到数据文件夹: {data_dir}")
            return None

        # 查找最新的raw_links_data文件
        links_files = [f for f in os.listdir(data_dir) if f.startswith('raw_links_data_') and f.endswith('.xlsx')]
        if not links_files:
            print("错误：未找到raw_links_data文件")
            return None

        # 按文件名排序（因为文件名包含时间戳）
        latest_file = sorted(links_files)[-1]
        links_file = os.path.join(data_dir, latest_file)
        print(f"正在处理最新的链接数据文件: {latest_file}")
        
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
        
        # 保存处理后的数据
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        output_file = os.path.join(data_dir, f"processed_links_{timestamp}.xlsx")
        df_result.to_excel(output_file, index=False)
        
        print("\n数据处理完成！")
        print(f"处理结果: {len(df_result)} 行")
        print(f"数据已保存至: {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    process_links_data()
 