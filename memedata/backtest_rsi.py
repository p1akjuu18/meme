import pandas as pd
import os
from datetime import datetime
import numpy as np

def backtest_rsi_strategy(df, rsi_buy=30, rsi_sell=70, initial_capital=10000):
    trades = []
    position = 0
    entry_price = 0
    all_trade_returns = []
    
    for index, row in df.iterrows():
        # RSI买入信号
        if row['rsi'] < rsi_buy and position == 0:
            position = 1
            entry_price = row['close']
            trades.append({
                '交易类型': '买入',
                '时间': row['timestamp'],
                '价格': row['close'],
                'RSI': row['rsi']
            })
            
        # RSI卖出信号
        elif row['rsi'] > rsi_sell and position == 1:
            position = 0
            exit_price = row['close']
            profit_pct = ((exit_price - entry_price) / entry_price) * 100
            all_trade_returns.append(profit_pct)
            
            # 打印每笔交易的信息
            print(f"\n交易详情:")
            print(f"买入价格: {entry_price}")
            print(f"卖出价格: {exit_price}")
            print(f"收益率: {profit_pct:.8f}%")
            
            trades.append({
                '交易类型': '卖出',
                '时间': row['timestamp'],
                '价格': row['close'],
                'RSI': row['rsi'],
                '收益率': f'{profit_pct:.2f}%',
                '收益率数值': profit_pct
            })
    
    # 打印所有交易收益率
    print("\n所有交易收益率:")
    for i, ret in enumerate(all_trade_returns, 1):
        print(f"交易 {i}: {ret:.8f}%")
    
    # 计算总收益率（直接相加所有交易收益率）
    total_returns = sum(all_trade_returns) if all_trade_returns else 0
    print(f"\n总收益率: {total_returns:.8f}%")
    
    # 计算最大回撤
    if all_trade_returns:
        cumsum_returns = np.cumsum(all_trade_returns)
        peak = np.maximum.accumulate(cumsum_returns)
        drawdowns = cumsum_returns - peak
        max_drawdown = np.min(drawdowns)
    else:
        max_drawdown = 0
    
    # 将交易记录转换为DataFrame
    trades_df = pd.DataFrame(trades)
    
    # 计算交易统计
    stats = {
        '总交易次数': 0,
        '胜率': '0.00%',
        '亏损交易数': 0,
        '小盈利(0-50%)': 0,
        '中等盈利(50-200%)': 0,
        '大盈利(>200%)': 0
    }
    
    if len(trades_df) > 0:
        sell_trades = trades_df[trades_df['交易类型'] == '卖出'].copy()
        if len(sell_trades) > 0:
            # 统计不同区间的交易次数
            loss_trades = len([r for r in all_trade_returns if r < 0])
            small_profit_trades = len([r for r in all_trade_returns if 0 <= r < 50])
            medium_profit_trades = len([r for r in all_trade_returns if 50 <= r < 200])
            large_profit_trades = len([r for r in all_trade_returns if r >= 200])
            
            total_trades = len(all_trade_returns)
            win_trades = total_trades - loss_trades
            win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
            
            stats.update({
                '总交易次数': total_trades,
                '胜率': f'{win_rate:.2f}%',
                '亏损交易数': loss_trades,
                '小盈利(0-50%)': small_profit_trades,
                '中等盈利(50-200%)': medium_profit_trades,
                '大盈利(>200%)': large_profit_trades
            })
    
    return {
        '总收益率': f'{total_returns:.2f}%',
        '最大回撤': f'{max_drawdown:.2f}%',
        '交易统计': stats,
        '交易记录': trades_df
    }

def run_backtest():
    try:
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        rsi_folder = os.path.join(desktop_path, 'token_rsi')
        
        if not os.path.exists(rsi_folder):
            print("RSI文件夹不存在！")
            return
        
        # 创建回测结果文件夹用于存储各个token的结果
        results_folder = os.path.join(desktop_path, 'backtest_results')
        os.makedirs(results_folder, exist_ok=True)
        
        # 存储所有币种的汇总结果
        all_results = []
        
        # 处理每个RSI文件
        for filename in os.listdir(rsi_folder):
            if filename.endswith('_RSI.csv'):
                try:
                    print(f"\n分析 {filename}")
                    file_path = os.path.join(rsi_folder, filename)
                    df = pd.read_csv(file_path)
                    
                    # 确保数据按时间排序
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.sort_values('timestamp')
                    
                    # 运行回测
                    results = backtest_rsi_strategy(df)
                    
                    # 提取币种名称
                    token_name = filename.replace('_RSI.csv', '')
                    
                    # 保存该币种的交易记录到backtest_results文件夹
                    trades_file = os.path.join(results_folder, f'{token_name}_trades.csv')
                    results['交易记录'].to_csv(trades_file, index=False, encoding='utf-8-sig')
                    
                    # 准备汇总结果
                    summary = {
                        '币种': token_name,
                        '总收益率': results['总收益率'],
                        '最大回撤': results['最大回撤'],
                        '总交易次数': results['交易统计']['总交易次数'],
                        '胜率': results['交易统计']['胜率'],
                        '亏损交易数': results['交易统计']['亏损交易数'],
                        '小盈利(0-50%)': results['交易统计']['小盈利(0-50%)'],
                        '中等盈利(50-200%)': results['交易统计']['中等盈利(50-200%)'],
                        '大盈利(>200%)': results['交易统计']['大盈利(>200%)']
                    }
                    all_results.append(summary)
                    
                    print(f"回测结果:")
                    for key, value in summary.items():
                        print(f"{key}: {value}")
                    print(f"详细交易记录已保存到: {trades_file}")
                    
                except Exception as e:
                    print(f"处理文件 {filename} 时出错: {str(e)}")
                    continue
        
        # 保存汇总结果到桌面
        try:
            summary_file = os.path.join(desktop_path, 'summary_results.csv')
            summary_df = pd.DataFrame(all_results)
            summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
            print(f"\n汇总结果已保存到桌面: {summary_file}")
            
            print("\n汇总结果预览:")
            print(summary_df)
            
        except Exception as e:
            print(f"保存汇总结果时出错: {str(e)}")
            print("\n打印汇总结果到控制台:")
            print(summary_df)
            
    except Exception as e:
        print(f"运行回测时出错: {str(e)}")

if __name__ == "__main__":
    run_backtest()
