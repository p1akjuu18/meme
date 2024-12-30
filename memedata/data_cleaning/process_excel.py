import pandas as pd
import re
import os
from collections import Counter
from datetime import datetime

# 设置固定的输入文件路径
desktop_path = os.path.expanduser("~/Desktop")
input_file = os.path.join(desktop_path, "raw_table_data_20250108_1652.xlsx")
if not os.path.exists(input_file):
    print(f"未找到输入文件: {input_file}")
    exit(1)

# 设置输出文件路径
desktop_path = os.path.expanduser("~/Desktop")
timestamp = datetime.now().strftime('%Y%m%d_%H%M')
output_file = os.path.join(desktop_path, f"clear_html_table_data_{timestamp}.xlsx")

# 读取Excel
try:
    df = pd.read_excel(input_file)
    print(f"成功读取文件: {input_file}")
except Exception as e:
    print(f"读取文件失败: {str(e)}")
    exit(1)

# 删除所有空的 Unnamed 列
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

def split_first_column(value):
    if pd.isna(value):
        return pd.Series({'币种': None, '最后活跃': None})
    
    value = str(value).strip()
    
    # 修改匹配模式，增加m选项
    time_match = re.search(r'\s*(\d+[mhd])$', value)
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
            if not re.search(r'\s+\d+[mhd]$', value):
                return pd.Series({'币种': value.lower(), '最后活跃': None})
        
        return pd.Series({
            '币种': coin_name.lower(),  # 转换为小写
            '最后活跃': time_value
        })
    
    # 如果没有匹配到时间格式，返回原值
    return pd.Series({'币种': value.lower(), '最后活跃': None})
def split_profit_column(value):
    if pd.isna(value):
        return pd.Series({'金额': None, '收益率': None})
    
    value = str(value)
    
    # 如果是"清仓"或者"$00%"或"持有"这样的特殊情况，直接返回原值和None
    if value in ['清仓', '$00%', '持有']:
        return pd.Series({'金额': value, '收益率': None})
    
    try:
        # 先尝试分离金额和百分比
        amount_part = ''
        percentage_part = ''
        
        # 处理金额部分（可能包含逗号和K/M/B）
        amount_match = re.match(r'^([+-]\$[\d,]+\.?\d*[KMB]?)', value)
        if amount_match:
            amount_part = amount_match.group(1)
            # 剩余部分应该是百分比
            percentage_part = value[len(amount_part):]
            
            # 检查百分比格式（现在允许包含K/M/B）
            if re.match(r'^[+-][\d.]+[KMB]?%$', percentage_part):
                # 处理金额中的逗号
                amount = amount_part.replace(',', '')
                return pd.Series({'金额': amount, '收益率': percentage_part})
    
    except Exception as e:
        print(f"处理值时出错: {value}, 错误: {str(e)}")
    
    # 如果没有匹配到任何格式或处理出错，返回原值
    return pd.Series({'金额': value, '收益率': None})

def split_trade_amount(value):
    if pd.isna(value):
        return pd.Series({'金额': None, '平均价': None})
    
    value = str(value)
    
    # 查找第二个$的位置
    first_dollar = value.find('$')
    if first_dollar != -1:
        second_dollar = value.find('$', first_dollar + 1)
        if second_dollar != -1:
            amount = value[:second_dollar].strip()
            avg_price = value[second_dollar:].strip()
            return pd.Series({'金额': amount, '平均价': avg_price})
    
    return pd.Series({'金额': value, '平均价': None})

def split_trade_count(value):
    if pd.isna(value):
        return pd.Series({'买入次数': None, '卖出次数': None})
    
    value = str(value)
    # 使用/分隔
    parts = value.split('/')
    if len(parts) == 2:
        return pd.Series({'买入次数': parts[0].strip(), '卖出次数': parts[1].strip()})
    return pd.Series({'买入次数': value, '卖出次数': None})

def extract_address(url):
    if pd.isna(url):
        return None
    
    # 使用正则表达式提取address/后面内容
    match = re.search(r'address/([^/\s]+)', str(url))
    if match:
        return match.group(1)
    return url

# 处理第一列（币种/最后活跃）
split_cols = df['币种/最后活跃'].apply(split_first_column)
df['币种'] = split_cols['币种']
df['最后活跃'] = split_cols['最后活跃']

# 处理未实现利润列
profit_cols = df['未实现利润'].apply(split_profit_column)
df['未实现金额'] = profit_cols['金额']
df['未实现收益率'] = profit_cols['收益率']

# 处理已实现利润列
realized_profit_cols = df['已实现利润'].apply(split_profit_column)
df['已实现金额'] = realized_profit_cols['金额']
df['已实现收益率'] = realized_profit_cols['收益率']

# 处理总买入/平均
buy_cols = df['总买入/平均'].apply(split_trade_amount)
df['总买入'] = buy_cols['金额']
df['买入平均价'] = buy_cols['平均价']

# 处理已卖出/平均
sell_cols = df['已卖出/平均'].apply(split_trade_amount)
df['已卖出'] = sell_cols['金额']
df['卖出平均价'] = sell_cols['平均价']

# 处理30D交易数
trade_cols = df['30D 交易数'].apply(split_trade_count)
df['30D买入次数'] = trade_cols['买入次数']
df['30D卖出次数'] = trade_cols['卖出次数']

# 处理Source URL
df['钱包地址'] = df['Source URL'].apply(extract_address)

# 在其他函数后添加处理总利润的函数
def split_total_profit(value):
    if pd.isna(value):
        return pd.Series({'总利润金额': None, '总利润率': None})
    
    value = str(value)
    
    try:
        # 处理金额部分（可能包含逗号和K/M/B）
        amount_match = re.match(r'^([+-]\$[\d,]+\.?\d*[KMB]?)', value)
        if amount_match:
            amount_part = amount_match.group(1)
            # 剩余部分应该是百分比
            percentage_part = value[len(amount_part):]
            
            # 检查百分比格式（允许包含K/M/B）
            if re.match(r'^[+-][\d.]+[KMB]?%$', percentage_part):
                # 处理金额中的逗号
                amount = amount_part.replace(',', '')
                return pd.Series({'总利润金额': amount, '总利润率': percentage_part})
    
    except Exception as e:
        print(f"处理总利润时出错: {value}, 错误: {str(e)}")
    
    return pd.Series({'总利润金额': value, '总利润率': None})

# 处理总利润列
total_profit_cols = df['总利润'].apply(split_total_profit)
df['总利润金额'] = total_profit_cols['总利润金额']
df['总利润率'] = total_profit_cols['总利润率']

# 新要删除的列
columns_to_drop = ['币种/最后活跃', '未实现利润', '已实现利润', 
                  '总买入/平均', '已卖出/平均', '30D 交易数', 
                  'Source URL', '余额USD', '总利润']

# 更新可用列列表
available_columns = ['币种', '最后活跃', 
                    '未实现金额', '未实现收益率',
                    '已实现金额', '已实现收益率',
                    '总利润金额', '总利润率',
                    '总买入', '买入平均价',
                    '已卖出', '卖出平均价',
                    '30D买入次数', '30D卖出次数',
                    '钱包地址']

# 只选择实际存在的列
columns_order = [col for col in available_columns if col in df.columns]
# 添加其他未在列表中的列
columns_order += [col for col in df.columns if col not in available_columns]

# 重新排列列顺序
df = df[columns_order]

# 过滤掉总买入为0的记录
df = df[df['总买入'] != '+$0']
df = df[df['总买入'] != '$0']

# 过滤掉未实现金额为"清仓"的记录
df = df[df['未实现金额'] != '清仓']

# 保存处理后的文件
df.to_excel(output_file, index=False, sheet_name="Processed Data")

print(f"处理后的数据已保存到: {output_file}")