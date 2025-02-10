import pandas as pd
import os
from datetime import datetime, timedelta

def analyze_token_holdings():
    # 获取data目录路径
    data_dir = os.path.join(os.getcwd(), 'data')
    
    # 查找最新的merged_token_data_文件
    merged_files = [f for f in os.listdir(data_dir) if f.startswith('merged_token_data_')]
    if not merged_files:
        print("未找到merged_token_data_开头的文件")
        return
        
    # 按文件名排序，获取最新的文件
    latest_file = sorted(merged_files)[-1]
    file_path = os.path.join(data_dir, latest_file)
    print(f"正在处理文件: {file_path}")
    
    # 读取文件
    df = pd.read_excel(file_path)
    
    # 将持仓%列转换为数值格式
    df['持仓 %'] = pd.to_numeric(df['持仓 %'].str.replace('%', ''), errors='coerce')
    
    # 删除持仓百分比为0或空白的记录
    df = df[df['持仓 %'].notna() & (df['持仓 %'] != 0)]
    # 删除代币地址为空的记录
    df = df[df['代币地址'].notna() & (df['代币地址'] != '')]
    print(f"清理后剩余记录数: {len(df)}")
    
    # 计算每个代币地址的钱包数量
    wallet_counts = df.groupby('代币地址')['钱包地址'].count().reset_index()
    wallet_counts = wallet_counts.rename(columns={'钱包地址': '买入钱包数'})
    
    # 计算每个代币的总余额
    total_balances = df.groupby('代币地址')['具体余额'].sum().reset_index()
    total_balances = total_balances.rename(columns={'具体余额': '聪明钱包总余额'})
    
    # 将钱包数量和总余额信息合并回原始数据
    df = pd.merge(df, wallet_counts, on='代币地址', how='left')
    df = pd.merge(df, total_balances, on='代币地址', how='left')
    
    # 删除聪明钱包总余额小于1000的记录
    df = df[df['聪明钱包总余额'] >= 1000]
    print(f"删除总余额<1000后剩余记录数: {len(df)}")
    
    # 只保留需要的列
    df = df[['币种', '代币地址', '买入钱包数', '聪明钱包总余额']]
    
    # 按代币地址去重
    df = df.drop_duplicates(subset=['代币地址'])
    
    # 按代币地址和买入钱包数排序
    df_sorted = df.sort_values(['买入钱包数', '代币地址'], ascending=[False, True])
    
    # 查找最新的token_query_results_all文件
    query_files = [f for f in os.listdir(data_dir) if f.startswith('token_query_results_all')]
    if query_files:
        latest_query_file = sorted(query_files)[-1]
        query_file_path = os.path.join(data_dir, latest_query_file)
        print(f"正在读取交易池信息: {query_file_path}")
        
        # 读取交易池信息
        pool_df = pd.read_excel(query_file_path)
        
        # 确保列名存在
        if '代币地址' in pool_df.columns and '交易池_地址' in pool_df.columns:
            # 创建代币地址到交易池地址和创建时间的映射
            pool_info = pool_df[['代币地址', '交易池_地址', '交易池_创建时间']].drop_duplicates()
            
            # 合并交易池信息
            df_sorted = pd.merge(df_sorted, pool_info, on='代币地址', how='left')
            
            # 计算代币存活天数
            current_time = datetime.now()
            df_sorted['代币存活天数'] = ((current_time - pd.to_datetime(df_sorted['交易池_创建时间'])).dt.total_seconds() / (24 * 3600)).astype(int)  # 转换为整数
            print("已添加交易池地址、创建时间和存活天数信息")
        else:
            print("交易池信息文件格式不正确")
    else:
        print("未找到token_query_results_all开头的文件")
        # 如果没有找到文件，添加空的交易池地址、创建时间和存活天数列
        df_sorted['交易池_地址'] = ''
        df_sorted['交易池_创建时间'] = None
        df_sorted['代币存活天数'] = None
    
    # 生成当前时间戳
    current_time = datetime.now().strftime('%Y%m%d')
    
    # 保存结果
    output_path = os.path.join(data_dir, f"token_data_sorted_{current_time}.xlsx")
    df_sorted.to_excel(output_path, index=False)
    
    print(f"\n结果已保存至: {output_path}")
    print(f"总计整理了 {len(df_sorted)} 个记录")
    
    return output_path

class TokenHoldingAnalyzer:
    def __init__(self):
        self.min_holding_time = timedelta(days=7)  # 最小持仓时间
        self.profit_threshold = 0.2  # 盈利阈值
        
    def analyze_holdings(self, holdings_data, trading_data):
        """分析持仓情况"""
        # 1. 识别长期持仓者
        long_term_holders = self.identify_long_term_holders(holdings_data)
        
        # 2. 分析交易盈利能力
        profitable_traders = self.analyze_trading_performance(trading_data)
        
        # 3. 识别聪明钱特征
        smart_money = self.identify_smart_money(long_term_holders, profitable_traders)
        
        return smart_money
        
    def identify_smart_money(self, holders, traders):
        """识别聪明钱"""
        smart_money_characteristics = {
            'long_term_holding': True,
            'profitable_trades': True,
            'large_position': True,
            'regular_accumulation': True
        }
        # 实现聪明钱识别逻辑

if __name__ == "__main__":
    analyze_token_holdings() 