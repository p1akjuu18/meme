import pandas as pd
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

class GMGNAnalyzer:
    def __init__(self, excel_path=None, json_path=None):
        self.excel_path = excel_path or os.path.join(
            os.path.expanduser("~"), 
            "Desktop", 
            "html_table_data20241222.xlsx"
        )
        self.json_path = json_path or os.path.join(
            os.path.expanduser("~"), 
            "Desktop", 
            "json_data20241222.json"
        )
        self.html_data = None
        self.json_data = None
        
    def load_data(self):
        """加载Excel和JSON数据"""
        try:
            self.html_data = pd.read_excel(self.excel_path)
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
            print("数据加载成功！")
        except Exception as e:
            print(f"数据加载失败：{str(e)}")
            
    def analyze_token_frequency(self):
        """分析代币出现频率"""
        if self.html_data is None:
            print("请先加载数据！")
            return
            
        token_counts = self.html_data['Token Name'].value_counts()
        return token_counts
        
    def plot_token_distribution(self, top_n=10):
        """绘制代币分布图表"""
        token_counts = self.analyze_token_frequency()
        plt.figure(figsize=(12, 6))
        sns.barplot(x=token_counts.head(top_n).values, 
                   y=token_counts.head(top_n).index)
        plt.title('代币出现频率分布（Top {}）'.format(top_n))
        plt.xlabel('出现次数')
        plt.ylabel('代币名称')
        plt.tight_layout()
        
        # 保存图表
        output_path = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            f"token_distribution_{datetime.now().strftime('%Y%m%d')}.png"
        )
        plt.savefig(output_path)
        print(f"图表已保存至：{output_path}")
        
    def analyze_json_data(self):
        """分析JSON数据中的特定模式"""
        if self.json_data is None:
            print("请先加载数据！")
            return
            
        analysis_results = {
            'total_addresses': len(self.json_data),
            'data_patterns': {}
        }
        
        for url, data in self.json_data.items():
            # 这里可以添加更多的分析逻辑
            try:
                props = data.get('props', {})
                page_props = props.get('pageProps', {})
                analysis_results['data_patterns'][url] = {
                    'has_pageProps': bool(page_props),
                    'data_timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                print(f"分析 {url} 时出错：{str(e)}")
                
        return analysis_results
    
    def export_analysis(self, analysis_results):
        """导出分析结果"""
        output_path = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            f"gmgn_analysis_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=4, ensure_ascii=False)
        print(f"分析结果已导出至：{output_path}")

def main():
    # 创建分析器实例
    analyzer = GMGNAnalyzer()
    
    # 加载数据
    analyzer.load_data()
    
    # 执行分析
    print("\n正在分析代币频率...")
    token_freq = analyzer.analyze_token_frequency()
    print("\n代币出现频率前10：")
    print(token_freq.head(10))
    
    # 绘制图表
    print("\n正在生成图表...")
    analyzer.plot_token_distribution()
    
    # 分析JSON数据
    print("\n正在分析JSON数据...")
    json_analysis = analyzer.analyze_json_data()
    
    # 导出分析结果
    analyzer.export_analysis(json_analysis)

if __name__ == "__main__":
    main() 