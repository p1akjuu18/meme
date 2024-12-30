import pandas as pd
import os

def clean_token_data(file_path):
    # 读取文件
    df = pd.read_excel(file_path)
    
    # 删除交易池_交易量_1小时为0的行
    df = df[df['交易池_交易量_1小时'] != 0]
    
    # 删除交易池_交易次数_1小时_卖出小于30的行
    df = df[df['交易池_交易次数_1小时_卖出'] >= 30]
    
    # 生成输出文件名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(os.path.expanduser("~"), "Desktop", f"{base_name}_cleaned.xlsx")
    
    # 保存数据为Excel格式
    df.to_excel(output_file, index=False)
    
    print(f"\n清洗后的数据已保存至: {output_file}")
    print(f"清洗后数据量: {len(df)} 行")
    
    return df

if __name__ == "__main__":
    # 获取桌面路径
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    file_name = "token_query_results_20250105_023946.xlsx"
    file_path = os.path.join(desktop, file_name)
    
    # 执行数据清洗
    cleaned_data = clean_token_data(file_path)
    
    # 显示基本统计信息
    print("\n数据基本信息：")
    print(cleaned_data.info())
    print("\n数据预览：")
    print(cleaned_data.head()) 