import pandas as pd
import os
import urllib.parse

def process_links_data():
    """处理链接数据文件"""
    try:
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        links_file = os.path.join(desktop_path, "raw_links_data_20241231_1256.xlsx")
        excel_file = os.path.join(desktop_path, "processed_tokens_20241231.xlsx")  # 另一个数据源
        
        if not os.path.exists(links_file):
            print(f"错误：未找到链接文件 {links_file}")
            return
            
        if not os.path.exists(excel_file):
            print(f"错误：未找到Excel文件 {excel_file}")
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
        
        # 处理Excel数据
        df_excel = pd.read_excel(excel_file)
        print(f"成功读取Excel数据，共 {len(df_excel)} 行")
        
        # 创建两个DataFrame
        df_links_result = pd.DataFrame(processed_links)
        
        # 合并数据
        # 如果Excel文件中的列名不同，需要先重命名
        if 'Token Address' not in df_excel.columns:
            df_excel = df_excel.rename(columns={
                df_excel.columns[0]: 'Token Address',
                df_excel.columns[1]: 'Token Name'
            })
        
        # 合并两个DataFrame
        df_combined = pd.concat([df_links_result, df_excel], ignore_index=True)
        
        # 去除重复数据
        df_combined = df_combined.drop_duplicates()
        
        # 保存合并后的数据
        output_file = os.path.join(desktop_path, "final_combined_tokens.xlsx")
        df_combined.to_excel(output_file, index=False)
        
        print("\n数据处理完成！")
        print(f"链接数据处理结果: {len(df_links_result)} 行")
        print(f"Excel数据处理结果: {len(df_excel)} 行")
        print(f"合并后的总数据: {len(df_combined)} 行")
        print(f"合并后的数据已保存至: {output_file}")
        
        # 显示前几行数据作为示例
        print("\n数据示例:")
        print(df_combined.head())
        
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_links_data() 