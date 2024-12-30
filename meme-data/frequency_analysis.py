import pandas as pd
from collections import Counter
import os
from datetime import datetime

class FrequencyAnalyzer:
    def __init__(self):
        self.desktop_path = os.path.expanduser("~/Desktop")
        
    def analyze_excel_frequency(self, file_name):
        """
        分析Excel文件中代币地址和名称的出现频次并输出到Excel
        
        参数:
            file_name: Excel文件名
        """
        file_path = os.path.join(self.desktop_path, file_name)
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return None
            
        try:
            df = pd.read_excel(file_path)
            required_columns = ['Token Address', 'Token Name', '30D买入次数']
            if not all(col in df.columns for col in required_columns):
                print("Excel文件中缺少必需的列")
                return None
            
            # 过滤30D买入次数大于0的记录
            df_filtered = df[df['30D买入次数'] > 0]
            
            return self._process_frequency(df_filtered[['Token Address', 'Token Name']])
        except Exception as e:
            print(f"处理Excel文件出错: {str(e)}")
            return None
    
    def _process_frequency(self, df):
        """
        处理代币地址和名称并计算频次，输出到Excel
        
        参数:
            df: 包含Token Address和Token Name的DataFrame
        """
        # 合并地址和名称为元组进行统计
        token_pairs = list(zip(df['Token Address'], df['Token Name']))
        frequency = Counter(token_pairs)
        
        # 按频次降序排序
        sorted_items = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
        
        # 创建DataFrame
        df_frequency = pd.DataFrame([
            {'Token地址': addr, 'Token名称': name, '出现次数': count}
            for (addr, name), count in sorted_items
        ])
        
        # 创建输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.desktop_path, f'token_frequency_{timestamp}.xlsx')
        
        # 保存到Excel
        df_frequency.to_excel(output_file, index=False, sheet_name='频次统计')
        
        print(f"\n统计结果已保存到: {output_file}")
        
        # 同时在控制台显示结果
        print("\n代币出现频次统计:")
        print("-" * 60)
        for (addr, name), count in sorted_items:
            if pd.notna(addr) and pd.notna(name):
                print(f"地址: {addr}, 名称: {name}, 出现次数: {count}次")
        
        return df_frequency

if __name__ == "__main__":
    analyzer = FrequencyAnalyzer()
    
    # 分析Excel文件
    print("\n分析Excel文件:")
    analyzer.analyze_excel_frequency("clear_html_table_data_20241229_1207.xlsx") 