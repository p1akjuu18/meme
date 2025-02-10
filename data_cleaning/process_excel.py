import pandas as pd
import re
import os
from collections import Counter
from datetime import datetime

def process_large_number(number_str):
    """处理大数字，根据位数决定保留的位数"""
    # 移除逗号和其他非数字字符
    clean_str = re.sub(r'[^\d.]', '', number_str)
    
    # 分割整数部分和小数部分
    parts = clean_str.split('.')
    integer_part = parts[0]
    
    # 根据整数部分的位数决定保留的位数
    length = len(integer_part)
    if length >= 5:
        keep_digits = max(2, length - 3)  # 5位数保留2位，6位数保留3位，以此类推
        return float(integer_part[:keep_digits])
    return float(integer_part)

def clean_number_with_unit(value):
    """
    清理带单位的数字，按照特定规则处理
    """
    if pd.isna(value):
        return 0
    
    # 检查原始值是否包含千分位
    has_comma = ',' in str(value)
    
    # 移除 $ 符号和逗号
    value = str(value).strip().replace('$', '').replace(',', '')
    
    try:
        # 处理类似 1.5M82433.69 的格式（保留M前面的数值并转换）
        complex_m_match = re.match(r'(\d+\.?\d*)M\d+.*', value)
        if complex_m_match:
            m_part = complex_m_match.group(1)
            return float(m_part) * 1000000

        # 新增：处理 $207.9K10M 这类格式（保留第一个K值并乘以1000）
        complex_k_match = re.match(r'(\d+\.?\d*)K\d+.*', value)  # 修改正则表达式，确保K后面有数字
        if complex_k_match:
            k_part = complex_k_match.group(1)
            return float(k_part) * 1000

        # 处理 K 结尾的数字
        k_match = re.match(r'(\d+\.?\d*)K$', value)  # 注意这里添加了 $ 确保是以K结尾
        if k_match:
            number_str = k_match.group(1)
            if not has_comma:  # 如果原始值没有千分位（如 776554.6K）
                number = str(int(float(number_str)))  # 转换为整数字符串
                return float(number[:3])  # 直接取前三位
            else:  # 如果原始值有千分位（如 6,288.46306K）
                if '.' in number_str:
                    parts = number_str.split('.')
                    return float(parts[0] + '.' + parts[1][:2])  # 保留两位小数
                return float(number_str)
                
        # 1. 处理 1M3.3K 或 1M8M 这类情况（保留第一个单位）
        if ('M' in value and 'K' in value) or ('M' in value and value.count('M') > 1):
            match = re.match(r'(\d+\.?\d*)(K|M)', value)
            if match:
                number = float(match.group(1))
                unit = match.group(2)
                if unit == 'K':
                    return number * 1000
                elif unit == 'M':
                    return number * 1000000
                
        # 2. 处理 51K210K 这类情况（保留第一个K值）
        if 'K' in value and value.count('K') > 1:
            match = re.match(r'(\d+\.?\d*)K', value)
            if match:
                return float(match.group(1)) * 1000
        
        # 3. 处理大数字M的情况（如 7,01810M）
        m_match = re.match(r'(\d+[,\d]*\.?\d*)M', value)
        if m_match:
            number_str = m_match.group(1)
            if float(re.sub(r'[^\d.]', '', number_str)) >= 10000:
                return process_large_number(number_str)
        
        # 5. 处理普通的多小数点情况（如 156.165.3M）
        if value.count('.') > 1:
            parts = value.split('.')
            number_str = parts[0] + '.' + parts[1][:2]
            return round(float(number_str), 2)
        
        # 6. 处理大数字（如 132,914.13）
        if '.' in value:
            number_str = re.sub(r'[^\d.]', '', value)
            integer_part = number_str.split('.')[0]
            if len(integer_part) >= 5:
                return process_large_number(integer_part)
        
        # 7. 处理普通数字
        number_str = re.sub(r'[^\d.]', '', value)
        if '.' in number_str:
            return round(float(number_str), 2)
        return float(number_str)
            
    except ValueError as e:
        print(f"无法处理的值: {value}, 错误: {e}")
        return 0
    except Exception as e:
        print(f"处理值时出错: {value}, 错误: {e}")
        return 0

# 主程序开始
if __name__ == "__main__":
    # 自动查找最新的数据文件
    data_dir = "data"  # 数据文件夹路径
    if not os.path.exists(data_dir):
        print(f"错误：未找到数据文件夹: {data_dir}")
        exit(1)

    # 查找最新的raw_table_data文件
    data_files = [f for f in os.listdir(data_dir) if f.startswith('raw_table_data_') and f.endswith('.xlsx')]
    if not data_files:
        print("错误：未找到raw_table_data文件")
        exit(1)

    # 按文件名排序（因为文件名包含时间戳）
    latest_file = sorted(data_files)[-1]
    input_file = os.path.join(data_dir, latest_file)
    print(f"正在处理最新的数据文件: {latest_file}")

    # 设置输出文件路径
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_file = os.path.join(data_dir, f"clear_html_table_data_{timestamp}.xlsx")

    # 读取Excel
    try:
        df = pd.read_excel(input_file, engine='openpyxl')
        print(f"成功读取文件: {input_file}")
        print("\n当前Excel文件的列名:")
        print(df.columns.tolist())
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
            time_part = time_match.group(0)
            symbol_part = value[:-len(time_part)].strip()
            return pd.Series({'币种': symbol_part, '最后活跃': time_part})
        else:
            return pd.Series({'币种': value, '最后活跃': None})

    # 处理第一列（币种/最后活跃）
    split_cols = df.iloc[:, 0].apply(split_first_column)
    df['币种'] = split_cols['币种']
    df['最后活跃'] = split_cols['最后活跃']
    
    # 删除原始的第一列
    df = df.drop(columns=[df.columns[0]])
    
    # 过滤掉币种为空的行
    df = df[df['币种'].notna()]
    
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

    # 处理未实现利润列
    profit_cols = df['未实现利润'].apply(split_profit_column)
    df['未实现金额'] = profit_cols['金额']
    df['未实现收益率'] = profit_cols['收益率']

    # 处理已实现利润列
    realized_profit_cols = df['已实现利润'].apply(split_profit_column)
    df['已实现金额'] = realized_profit_cols['金额']
    df['已实现收益率'] = realized_profit_cols['收益率']

    # 处理总买入/平均列
    buy_cols = df['总买入/平均'].apply(split_trade_amount)
    df['总买入'] = buy_cols['金额']
    df['买入平均价'] = buy_cols['平均价']

    # 处理总卖出/平均列
    sell_cols = df['总卖出/平均'].apply(split_trade_amount)
    df['总卖出'] = sell_cols['金额']
    df['卖出平均价'] = sell_cols['平均价']

    # 处理30D交易数列
    trade_cols = df['30D 交易数'].apply(split_trade_count)
    df['30D买入次数'] = trade_cols['买入次数']
    df['30D卖出次数'] = trade_cols['卖出次数']

    # 处理Source URL列
    df['钱包地址'] = df['Source URL'].apply(extract_address)

    # 处理总利润列
    total_profit_cols = df['总利润'].apply(split_profit_column)
    df['总利润金额'] = total_profit_cols['金额']
    df['总利润率'] = total_profit_cols['收益率']

    # 复制"余额USD"列数据到新的"具体余额"列
    df['具体余额'] = df['余额USD'].copy()

    # 处理"具体余额"列的数据
    print("正在处理余额数据...")
    df['具体余额'] = df['具体余额'].apply(clean_number_with_unit)

    # 新要删除的列
    columns_to_drop = ['未实现利润', '已实现利润', 
                      '总买入/平均', '总卖出/平均', '30D 交易数', 
                      'Source URL', '余额USD', '总利润']

    # 删除不需要的列
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

    # 更新可用列列表
    available_columns = ['币种', '最后活跃', 
                        '未实现金额', '未实现收益率',
                        '已实现金额', '已实现收益率',
                        '总利润金额', '总利润率',
                        '总买入', '买入平均价',
                        '总卖出', '卖出平均价',
                        '30D买入次数', '30D卖出次数',
                        '钱包地址', '具体余额']

    # 只选择实际存在的列
    columns_order = [col for col in available_columns if col in df.columns]
    # 添加其他未在列表中的列
    columns_order += [col for col in df.columns if col not in available_columns]

    # 重新排列列顺序
    df = df[columns_order]

    # 过滤掉总买入为0的记录
    df = df[df['总买入'] != '+$0']
    df = df[df['总买入'] != '$0']

    # 过滤掉已清仓的记录（当未实现金额显示为"清仓"时，表示该币种已经被完全卖出，应该删除整行数据）
    df = df[df['未实现金额'] != '清仓']

    # 过滤掉具体余额为0的记录
    df = df[df['具体余额'] != 0]

    # 保存处理后的文件
    df.to_excel(output_file, index=False)

    print(f"\n处理后的数据已保存到: {output_file}")
    print("文件包含处理后的数据")