import pandas as pd
import os
import re

def clean_number_with_unit(value):
    """
    清理带单位的数字，处理特殊格式
    例如：
    $6036.352M -> 6036.35
    $12.881.2M -> 12.88
    $14.7K3.3M -> 14700 (14.7K)
    26.61788.2K -> 26.61
    1,485.3415.7M -> 1485.34
    0.1881,000 -> 0.18
    """
    if pd.isna(value):
        return 0
    
    # 移除 $ 符号和逗号
    value = str(value).strip().replace('$', '').replace(',', '')
    
    try:
        # 特殊处理 K3.3M 这种情况
        if 'K' in value and 'M' in value:
            k_part = value.split('K')[0]
            number = float(k_part) * 1000
            return round(number, 2)
        
        # 处理普通情况
        parts = value.split('.')
        if len(parts) > 1:
            # 保留第一个小数点前的部分和第一个小数点后的两位
            number_str = parts[0] + '.' + parts[1][:2]
            
            # 移除所有字母和其他特殊字符，保留数字和小数点
            number_str = re.sub(r'[^\d.]', '', number_str)
            result = round(float(number_str), 2)
            
            # 如果原始值包含 K，需要乘以 1000
            if 'K' in value:
                result *= 1000
                
            return result
        else:
            # 处理没有小数点的情况
            number_str = re.sub(r'[^\d.]', '', value)
            return round(float(number_str), 2)
            
    except ValueError as e:
        print(f"无法处理的值: {value}, 错误: {e}")
        return 0
    except Exception as e:
        print(f"处理值时出错: {value}, 错误: {e}")
        return 0

def process_excel_data(input_file: str, output_file: str = None):
    """
    处理Excel数据的主函数
    
    参数:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选，默认为在输入文件名后加上'_processed'）
    """
    try:
        if not output_file:
            # 自动生成输出文件名
            file_name, file_ext = os.path.splitext(input_file)
            output_file = f"{file_name}_processed{file_ext}"
            
        # 步骤1：读取原始文件并删除"清仓"数据
        print("\n步骤1：删除'清仓'数据")
        df = pd.read_excel(input_file)
        print(f"原始数据行数: {len(df)}")
        
        # 删除"未实现金额"列为"清仓"的行
        df = df[df["未实现金额"] != "清仓"]
        print(f"删除'清仓'后数据行数: {len(df)}")
        
        # 步骤2：添加"持有钱包数"列
        print("\n步骤2：添加'持有钱包数'列")
        wallet_counts = df.iloc[:, 1].value_counts()
        df['持有钱包数'] = df.iloc[:, 1].map(wallet_counts)
        print(f"最大持有钱包数: {df['持有钱包数'].max()}")
        print(f"平均持有钱包数: {df['持有钱包数'].mean():.2f}")
        
        # 步骤3：添加"聪明钱包总余额"列
        print("\n步骤3：添加'聪明钱包总余额'列")
        df['处理后余额'] = df.iloc[:, 20].apply(clean_number_with_unit)
        
        # 计算相同钱包地址对应的处理后余额总和
        wallet_balances = df.groupby(df.iloc[:, 1])['处理后余额'].sum()
        df['聪明钱包总余额'] = df.iloc[:, 1].map(wallet_balances)
        
        # 删除临时列
        df = df.drop('处理后余额', axis=1)
        
        # 保存处理后的数据
        df.to_excel(output_file, index=False)
        print(f"\n处理完成！")
        print(f"最终文件已保存为: {output_file}")
        print(f"最终数据行数: {len(df)}")
        
        return df
        
    except FileNotFoundError:
        print(f"错误：找不到文件 '{input_file}'")
        print("请确保Excel文件路径正确")
    except Exception as e:
        print(f"处理过程中出错: {e}")
        import traceback
        print(traceback.format_exc())
        
if __name__ == "__main__":
    try:
        # 获取桌面路径
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        input_file = os.path.join(desktop, "token_data_sorted_202501088.xlsx")
        
        # 检查文件是否存在
        if not os.path.exists(input_file):
            print(f"错误：文件不存在: {input_file}")
            print("请确保Excel文件在桌面上")
            exit(1)
            
        print("开始处理数据...")
        print(f"使用的输入文件: {input_file}")
        
        # 设置输出文件也保存到桌面
        output_file = os.path.join(desktop, "token_data_sorted_2025010888.xlsx")
        process_excel_data(input_file, output_file)
        
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        print(traceback.format_exc()) 