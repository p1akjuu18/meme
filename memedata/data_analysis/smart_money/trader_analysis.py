import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class TraderAnalysis:
    def __init__(self, df, top_traders):
        self.df = df
        self.top_traders = top_traders
        
    def analyze_trading_pattern(self, address):
        """分析特定地址的交易模式"""
        trader_data = self.top_traders[self.top_traders['address'] == address]
        
        # 检查是否找到数据
        if len(trader_data) == 0:
            return {
                '错误': f'未找到地址 {address} 的数据'
            }
            
        analysis = {
            '基本信息': self._analyze_basic_info(trader_data),
            '交易表现': self._analyze_performance(trader_data),
            '交易频率': self._analyze_trading_frequency(trader_data),
            '收益分布': self._analyze_profit_distribution(trader_data),
            '社交数据': self._analyze_social_metrics(trader_data)
        }
        return analysis
    
    def _analyze_basic_info(self, trader_data):
        """分析基本信息"""
        data = trader_data.iloc[0]
        info = {
            '地址': data['address'],
            'SOL余额': f"{data['sol_balance']:.2f} SOL"
        }
        return info
    
    def _analyze_performance(self, trader_data):
        """分析交易表现"""
        data = trader_data.iloc[0]
        return {
            '总收益': f"${data['pnl']:.2f}",
            '7天收益': f"${data['pnl_7d']:.2f}",
            '30天收益': f"${data['pnl_30d']:.2f}",
            '7天已实现收益': f"${data['realized_profit_7d']:.2f}",
            '30天已实现收益': f"${data['realized_profit_30d']:.2f}",
            '总累计收益': f"${data['all_pnl']:.2f}",
            '总实现收益': f"${data['total_profit_pnl']:.2f}"
        }
    
    def _analyze_trading_frequency(self, trader_data):
        """分析交易频率"""
        data = trader_data.iloc[0]
        return {
            '30天买入次数': int(data['buy_30d']),
            '30天卖出次数': int(data['sell_30d']),
            '7天买入次数': int(data['buy_7d']),
            '7天卖出次数': int(data['sell_7d']),
            '月均交易频率': f"{(data['buy_30d'] + data['sell_30d']) / 2:.1f}次"
        }
    
    def _analyze_profit_distribution(self, trader_data):
        """分析收益分布"""
        data = trader_data.iloc[0]
        dist = {}
        
        profit_fields = {
            'pnl_lt_minus_dot5_num': '亏损超50%',
            'pnl_minus_dot5_0x_num': '亏损0-50%',
            'pnl_lt_2x_num': '盈利0-200%',
            'pnl_2x_5x_num': '盈利200-500%',
            'pnl_gt_5x_num': '盈利超500%'
        }
        
        for field, label in profit_fields.items():
            if field in data:
                dist[label] = int(data[field])
            
        return dist
    
    def _analyze_social_metrics(self, trader_data):
        """分析社交指标"""
        data = trader_data.iloc[0]
        social_info = {
            'Twitter绑定': '是' if data['twitter_bind'] else '否',
            'Twitter粉丝数': int(data['twitter_fans_num']) if pd.notna(data['twitter_fans_num']) else 0
        }
        
        if pd.notna(data['twitter_username']):
            social_info['Twitter用户名'] = data['twitter_username']
        if pd.notna(data['twitter_name']):
            social_info['Twitter昵称'] = data['twitter_name']
        
        return social_info
    
    def generate_trading_report(self):
        """为所有top交易者生成分析报告"""
        reports = {}
        for address in self.top_traders['address'].values:
            try:
                reports[address] = self.analyze_trading_pattern(address)
            except Exception as e:
                print(f"处理地址 {address} 时出错: {str(e)}")
                reports[address] = {'错误': f'处理数据时出错: {str(e)}'}
        return reports 
    
    def format_analysis_report(self, reports):
        """格式化分析报告"""
        formatted_reports = {}
        for address, report in reports.items():
            formatted = {
                '基础信息': {
                    '地址': address,
                    'Twitter': report['社交数据'].get('Twitter用户名', '未绑定'),
                    'SOL余额': report['基本信息']['SOL余额']
                },
                '交易表现': {
                    '30天收益': report['交易表现']['30天收益'],
                    '总收益': report['交易表现']['总收益'],
                    '胜率': report['交易表现']['胜率']
                },
                '交易特征': {
                    '��易频率': report['交易频率']['月均交易频率'],
                    '代币数量': report['基本信息']['交易代币数'],
                    '盈利代币': report['基本信息']['盈利代币数']
                }
            }
            formatted_reports[address] = formatted
        return formatted_reports 