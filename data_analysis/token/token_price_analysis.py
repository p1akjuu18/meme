import pandas as pd
import os
import logging
import traceback
from datetime import datetime, timedelta

# 配置日志
logger = logging.getLogger('TokenPriceAnalysis')
if not logger.handlers:  # 避免重复配置
    logger.setLevel(logging.WARNING)  # 默认级别改为WARNING
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    # 添加文件处理器，记录所有日志
    file_handler = logging.FileHandler('logs/token_price_analysis.log', encoding='utf-8', mode='a')
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别的日志
    logger.addHandler(file_handler)
    
    # 添加控制台处理器，只显示重要信息
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    console_handler.setLevel(logging.WARNING)  # 控制台只显示WARNING及以上级别
    logger.addHandler(console_handler)
    
    logger.propagate = False  # 阻止日志传播到父logger

def analyze_token_data(folder_path, output_folder=None):
    results = []
    
    # 检查并记录文件夹内容
    logger.debug(f"开始分析文件夹: {folder_path}")
    try:
        files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        logger.debug(f"找到 {len(files)} 个CSV文件")
        if not files:
            logger.error(f"在{folder_path}中没有找到CSV文件")
            return None
    except Exception as e:
        logger.error(f"读取文件夹出错: {str(e)}")
        return None
    
    # 遍历文件夹中的所有文件
    processed_count = 0
    error_count = 0
    
    for filename in files:
        try:
            # 读取CSV文件
            df = pd.read_csv(os.path.join(folder_path, filename))
            
            # 确保有必要的列
            required_columns = ['timestamp', 'high', 'close', 'low']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"{filename} 缺少必要的列")
                error_count += 1
                continue
            
            # 检查数据是否为空
            if df.empty:
                logger.error(f"{filename} 数据为空")
                error_count += 1
                continue
                
            # 转换timestamp为datetime
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except Exception as e:
                logger.error(f"{filename} 时间戳转换失败")
                error_count += 1
                continue
            
            # 获取开始时间后15分钟的时间点
            start_time = df['timestamp'].min()
            cutoff_time = start_time + timedelta(minutes=15)
            
            # 过滤掉前15分钟的数据
            df_filtered = df[df['timestamp'] > cutoff_time].copy()
            
            if len(df_filtered) > 0:
                # 找到最高价和对应时间
                max_price = df_filtered['high'].max()
                max_price_idx = df_filtered['high'].idxmax()
                max_price_time = df_filtered.loc[max_price_idx, 'timestamp']
                
                # 只看最高价之后的数据来计算回调
                df_after_high = df_filtered.loc[max_price_idx:].copy()
                
                if len(df_after_high) > 1:  # 确保最高价后还有数据
                    lowest_after_high = df_after_high['low'].min()
                    max_drawdown = (max_price - lowest_after_high) / max_price * 100
                    lowest_time = df_after_high.loc[df_after_high['low'].idxmin(), 'timestamp']
                else:
                    max_drawdown = 0
                    lowest_time = max_price_time
                
                # 存储结果
                token_name = filename.replace('.csv', '')
                results.append({
                    'token': token_name,
                    'max_price': max_price,
                    'max_price_time': max_price_time,
                    'lowest_after_high': lowest_after_high if len(df_after_high) > 1 else max_price,
                    'lowest_time': lowest_time,
                    'max_drawdown_percentage': max_drawdown,
                    'analysis_start_time': cutoff_time,
                    'initial_price': df_filtered['close'].iloc[0],
                    'final_price': df_filtered['close'].iloc[-1],
                    'data_points': len(df_filtered)
                })
                processed_count += 1
                logger.debug(f"处理完成: {filename}")
            else:
                logger.debug(f"{filename} 过滤后无数据")
                error_count += 1
            
        except Exception as e:
            logger.error(f"处理失败 {filename}: {str(e)}")
            error_count += 1
    
    logger.debug(f"处理完成: 成功 {processed_count} 个, 失败 {error_count} 个")
    
    # 如果结果不为空，创建DataFrame并保存
    if results:
        df_results = pd.DataFrame(results)
        
        # 计算统计信息
        total_tokens = len(df_results)
        min_drawdown = df_results['max_drawdown_percentage'].min()
        max_drawdown = df_results['max_drawdown_percentage'].max()
        avg_drawdown = df_results['max_drawdown_percentage'].mean()
        
        # 打印统计信息（简化版本）
        logger.debug(f"分析统计: {total_tokens}个代币, 回调范围 {min_drawdown:.1f}%-{max_drawdown:.1f}%, 平均{avg_drawdown:.1f}%")
        
        # 如果指定了输出文件夹，保存结果
        if output_folder:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(output_folder, f'price_analysis_{timestamp}.csv')
            df_results.to_csv(output_path, index=False, encoding='utf-8')
            logger.debug(f"结果已保存: {output_path}")
        
        return df_results
    else:
        logger.warning("无可分析数据")
        return None

def main():
    # 设置数据文件夹路径 - 使用项目根目录下的data/token
    current_dir = os.path.dirname(os.path.abspath(__file__))  # token目录
    project_root = os.path.dirname(os.path.dirname(current_dir))  # 项目根目录
    data_folder = os.path.join(project_root, "data")  # data文件夹
    token_folder = os.path.join(data_folder, "token")  # token文件夹
    
    # 检查文件夹是否存在
    if not os.path.exists(token_folder):
        logger.error(f"错误：找不到文件夹 {token_folder}")
        logger.error(f"当前目录: {current_dir}")
        return
    
    # 分析数据
    results = analyze_token_data(token_folder)
    
    # 格式化输出
    if results is not None and not results.empty:
        logger.info("\n=== 价格分析统计 ===")
        logger.info(f"分析代币总数: {len(results)}")
        logger.info(f"最大回调范围: {results['max_drawdown_percentage'].min():.2f}% - {results['max_drawdown_percentage'].max():.2f}%")
        logger.info(f"平均最大回调: {results['max_drawdown_percentage'].mean():.2f}%")
        
        # 直接保存在data文件夹下
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        output_path = os.path.join(data_folder, f"price_analysis_results_{timestamp}.csv")
        results.to_csv(output_path, index=False, encoding='utf-8')
        logger.debug(f"分析结果已保存到data文件夹: {output_path}")
    else:
        logger.warning("没有找到可分析的数据")

if __name__ == "__main__":
    main() 