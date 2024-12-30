import pandas as pd
import numpy as np

class TraderScorer:
    def __init__(self, df):
        self.df = df
        self.scores = pd.DataFrame()
        
    def calculate_profit_score(self, weights={
        'pnl': 0.5,          # 总体盈利能力权重提高到50%
        'pnl_7d': 0.2,       # 降低短期权重
        'pnl_30d': 0.3       # 保持中期权重
    }):
        """计算盈利能力得分，更重视总体盈利能力"""
        # 对每个指标进行归一化处理
        for col in ['pnl', 'pnl_7d', 'pnl_30d']:
            normalized = (self.df[col] - self.df[col].min()) / (self.df[col].max() - self.df[col].min())
            self.scores[f'{col}_score'] = normalized * weights[col] * 100
            
        self.scores['profit_score'] = self.scores[[f'{col}_score' for col in weights.keys()]].sum(axis=1)
        
    def calculate_trading_frequency_score(self, weights={
        'recent': 0.3,    # 降低短期交易频率权重
        'longer': 0.7     # 提高长期交易频率权重
    }):
        """计算交易频率得分，更重视低频稳健交易"""
        # 计算交易频率
        self.df['trade_freq_7d'] = self.df['buy_7d'] + self.df['sell_7d']
        self.df['trade_freq_30d'] = self.df['buy_30d'] + self.df['sell_30d']
        
        # 对交易频率进行反向评分（频率越低分数越高）
        for col, period in [('trade_freq_7d', 'recent'), ('trade_freq_30d', 'longer')]:
            # 反转归一化：用最大值减去当前值
            max_freq = self.df[col].max()
            normalized = (max_freq - self.df[col]) / (max_freq - self.df[col].min())
            self.scores[f'{col}_score'] = normalized * weights[period] * 100
            
        self.scores['frequency_score'] = self.scores[[f'{col}_score' for col in ['trade_freq_7d', 'trade_freq_30d']]].sum(axis=1)
        
    def calculate_portfolio_quality_score(self):
        """计算投资组合质量得分"""
        # 计算盈利代币占比
        self.df['profit_ratio'] = self.df['profit_num'] / self.df['token_num']
        
        # 计算不同盈利区间的得分
        profit_weights = {
            'pnl_lt_minus_dot5_num': -2,     # 亏损>50%，严重惩罚
            'pnl_minus_dot5_0x_num': -1,     # 亏损0-50%，轻微惩罚
            'pnl_lt_2x_num': 1,              # 盈利0-200%，基础奖励
            'pnl_2x_5x_num': 2,              # 盈利200-500%，较高奖励
            'pnl_gt_5x_num': 3               # 盈利>500%，高额奖励
        }
        
        # 计算加权得分
        weighted_score = sum(self.df[col] * weight for col, weight in profit_weights.items())
        normalized_score = (weighted_score - weighted_score.min()) / (weighted_score.max() - weighted_score.min())
        
        self.scores['portfolio_score'] = normalized_score * 100
        
    def calculate_final_score(self, weights={
        'profit': 0.5,      # 提高盈利能力权重到50%
        'frequency': 0.3,   # 保持交易频率权重
        'portfolio': 0.2    # 降低投资组合权重
    }):
        """计算最终综合得分"""
        self.calculate_profit_score()
        self.calculate_trading_frequency_score()
        self.calculate_portfolio_quality_score()
        
        self.scores['final_score'] = (
            self.scores['profit_score'] * weights['profit'] +
            self.scores['frequency_score'] * weights['frequency'] +
            self.scores['portfolio_score'] * weights['portfolio']
        )
        
    def get_top_traders(self, top_n=20):
        """获取得分最高的交易者"""
        # 保持address作为普通列，只选择必需和非空的列
        result = pd.merge(
            self.df[[
                'address', 
                'twitter_username', 
                'twitter_name', 
                'sol_balance',
                'pnl', 'pnl_7d', 'pnl_30d',
                'realized_profit_7d', 'realized_profit_30d',
                'all_pnl', 'total_profit_pnl',
                'buy_30d', 'sell_30d',
                'buy_7d', 'sell_7d',
                'twitter_bind', 'twitter_fans_num'
            ]],
            self.scores,
            left_index=True,
            right_index=True
        )
        return result.sort_values('final_score', ascending=False).head(top_n) 