import pandas as pd
import re
import os
from collections import Counter
from datetime import datetime
import urllib.parse

# 设置输入输出文件路径
desktop_path = os.path.expanduser("~/Desktop")
input_file = os.path.join(desktop_path, "raw_table_data_20241231_1256.xlsx")
timestamp = datetime.now().strftime('%Y%m%d_%H%M')
output_file = os.path.join(desktop_path, f"clear_html_table_data_{timestamp}.xlsx")

# 读取Excel
try:
    df = pd.read_excel(input_file)
    print(f"成功读取文件: {input_file}")
except Exception as e:
    print(f"读取文件失败: {str(e)}")
    exit(1)

def split_first_column(value):
    if pd.isna(value):
        return pd.Series({'币种': None, '最后活跃': None})
    
    value = str(value).strip()
    
    # 匹配最后的数字+h/d部分，允许前面有空格
    time_match = re.search(r'\s*(\d+[hd])$', value)
    if time_match:
        time_value = time_match.group(1)
        # 获取时间值之前的所有内容作为币种名称，并去除尾部空格
        coin_name = value[:-len(time_match.group(0))].strip()
        
        # 如果币种名称为空（比如只有表情），则保留原始值
        if not coin_name:
            coin_name = value[:-len(time_value)].strip()
        
        # 处理特殊情况：如果币种名称数字结尾，确保它是有效的
        if re.search(r'\d+$', coin_name):
            # 检查是否有空格分隔，如果没有，可能是误分割
            if not re.search(r'\s+\d+[hd]$', value):
                return pd.Series({'币种': value.lower(), '最后活跃': None})
        
        return pd.Series({
            '币种': coin_name.lower(),  # 转换为小写
            '最后活跃': time_value
        })
    
    # 如果没有匹配到时间格式，返回原值
    return pd.Series({'币种': value.lower(), '最后活跃': None})

def split_profit_column(value):
    """处理利润列"""
    # [保持原函数内容不变]

def split_trade_amount(value):
    """处理交易金额列"""
    # [保持原函数内容不变]

def split_trade_count(value):
    """处理交易次数列"""
    # [保持原函数内容不变]

def extract_address(url):
    """提取地址"""
    # [保持原函数内容不变]

def split_total_profit(value):
    """处理总利润列"""
    # [保持原函数内容不变]

def process_excel_data():
    """处理Excel表格数据"""
    try:
        # 从环境变量获取输入文件路径
        input_file = os.getenv('EXCEL_INPUT_FILE')
        if not input_file:
            print("未找到输入文件路径")
            return None
            
        # 读取Excel
        df = pd.read_excel(input_file)
        print(f"成功读取Excel文件: {input_file}")
        
        # 删除所有空的 Unnamed 列
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # 提取钱包地址
        df['钱包地址'] = df['Source URL'].apply(lambda x: re.search(r'address/([^/\s]+)', str(x)).group(1) if re.search(r'address/([^/\s]+)', str(x)) else x)
        
        # 保留需要的列
        if '币种' in df.columns:
            result_df = df[['币种', '钱包地址']].copy()
            result_df = result_df.rename(columns={'币种': 'Token Name', '钱包地址': 'Token Address'})
            return result_df
            
    except Exception as e:
        print(f"处理Excel数据时出错: {str(e)}")
        return None

def analyze_token_frequency(df):
    """分析代币频次"""
    # [保持原函数内容不变]

# 链接数据处理相关函数
def process_links():
    """处理链接数据文件"""
    try:
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        links_file = os.path.join(desktop_path, "raw_links_data_20241231_1256.xlsx")
        
        if not os.path.exists(links_file):
            print(f"错误：未找到链接文件 {links_file}")
            return None
        
        # 读取链接数据
        df_links = pd.read_excel(links_file)
        print(f"成功读取链接数据，共 {len(df_links)} 行")
        
        # 按3行一组处理数据
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
        
        return pd.DataFrame(processed_links)
        
    except Exception as e:
        print(f"处理链接数据时出错: {str(e)}")
        return None

if __name__ == "__main__":
    if input_file:
        analyze_token_frequency(output_file)
        
        # 处理链接数据
        df_links = process_links()
        if df_links is not None:
            print(f"\n链接数据处理完成，共 {len(df_links)} 行")
            
            # 读取之前处理好的Excel数据
            df_excel = pd.read_excel(output_file)
            
            # 合并数据
            df_combined = pd.concat([df_links, df_excel], ignore_index=True)
            df_combined = df_combined.drop_duplicates()
            
            # 保存最终结果
            final_output = os.path.join(desktop_path, f"final_combined_data_{timestamp}.xlsx")
            df_combined.to_excel(final_output, index=False)
            
            print(f"\n最终数据已保存至: {final_output}")
            print(f"合并后的总数据量: {len(df_combined)} 行") 