import pandas as pd
from collections import Counter
import os

def analyze_token_frequency(file_path):
    """
    分析Excel文件中代币名称的出现频次
    
    参数:
        file_path: Excel文件路径
    返回:
        dict: 排序后的频次统计
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
        
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 检查'币种'列是否存在
        if '币种' not in df.columns:
            print("Excel文件中没有'币种'列")
            return None
        
        # 获取币种列的数据
        token_names = df['币种'].tolist()
        
        # 统计频次
        frequency = Counter(token_names)
        
        # 按频次降序排序
        sorted_frequency = dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True))
        
        # 打印结果
        print("\n代币出现频次统计:")
        print("-" * 40)
        for token, count in sorted_frequency.items():
            if pd.notna(token):  # 使用pandas的notna函数来检查是否为空值
                print(f"{token}: {count}次")
        
        return sorted_frequency
        
    except pd.errors.EmptyDataError:
        print("Excel文件为空")
        return None
    except pd.errors.ParserError:
        print("Excel文件格式错误")
        return None
    except Exception as e:
        print(f"处理出错: {str(e)}")
        return None

if __name__ == "__main__":
    # 获取桌面路径
    desktop_path = os.path.expanduser("~/Desktop")
    file_path = os.path.join(desktop_path, "processed_data20241222.xlsx")
    
    analyze_token_frequency(file_path) 