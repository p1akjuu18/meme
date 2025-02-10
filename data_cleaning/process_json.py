import pandas as pd
import json
import os
from datetime import datetime

def process_json_data():
    try:
        # 使用data目录
        data_dir = "data"
        if not os.path.exists(data_dir):
            print(f"错误：未找到数据文件夹: {data_dir}")
            return

        # 查找最新的raw_json_data文件
        json_files = [f for f in os.listdir(data_dir) if f.startswith('raw_json_data_') and f.endswith('.json')]
        if not json_files:
            print("错误：未找到raw_json_data文件")
            return

        # 按文件名排序（因为文件名包含时间戳）
        latest_file = sorted(json_files)[-1]
        input_file = os.path.join(data_dir, latest_file)
        print(f"正在处理最新的JSON数据文件: {latest_file}")

        # 读取JSON数据
        with open(input_file, 'r', encoding='utf-8') as file:
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

        # 设置输出文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        output_file = os.path.join(data_dir, f"processed_json_{timestamp}.xlsx")

        # 保存到Excel
        df.to_excel(output_file, index=False)
        print(f"数据已成功保存到: {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"处理JSON数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    process_json_data() 