import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import os
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,  # 保持INFO级别以显示重要信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupportResistanceAnalyzer:
    """
    支撑位和阻力位分析器
    """
    def __init__(self, data_folder: str):
        self.data_folder = data_folder
        self.support_levels = {}
        self.current_prices = {}
        
    def load_token_data(self, token_symbol: str) -> pd.DataFrame:
        """
        加载单个代币的历史数据
        """
        try:
            # 查找匹配的文件
            matching_files = [f for f in os.listdir(self.data_folder) 
                            if f.startswith(token_symbol.split('_')[0]) and f.endswith('.csv')]
            
            if not matching_files:
                logger.info(f"跳过 {token_symbol} - 未找到数据文件")
                return None
                
            # 使用最新的文件（按文件名排序，取最后一个）
            latest_file = sorted(matching_files)[-1]
            file_path = os.path.join(self.data_folder, latest_file)
            
            df = pd.read_csv(file_path)
            
            # 检查必要的列是否存在
            required_columns = ['timestamp', 'close']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.info(f"跳过 {token_symbol} - 数据不完整")
                return None

            # 如果timestamp列不存在，尝试其他可能的列名
            timestamp_alternatives = ['time', 'date', 'datetime']
            if 'timestamp' not in df.columns:
                for alt in timestamp_alternatives:
                    if alt in df.columns:
                        df['timestamp'] = df[alt]
                        break
                
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # 按时间戳排序
            df = df.sort_values('timestamp', ascending=True)
            logger.info(f"加载 {token_symbol} - {len(df)}行数据")
            return df
        except Exception as e:
            logger.error(f"加载 {token_symbol} 数据失败: {str(e)}")
            return None

    def find_local_minima(self, prices: np.array, window: int = 20) -> List[int]:
        """
        使用纯numpy找出局部最小值
        """
        indices = []
        for i in range(window, len(prices) - window):
            if all(prices[i] <= prices[i-window:i]) and \
               all(prices[i] <= prices[i+1:i+window+1]):
                indices.append(i)
        return indices

    def merge_support_levels(self, support_prices: np.array, threshold: float = 0.20) -> List[Dict]:
        """
        合并接近的支撑位并统计频次
        
        Args:
            support_prices: 原始支撑位价格数组
            threshold: 合并阈值，默认20%
            
        Returns:
            List[Dict]: 包含合并后的支撑位信息，每个字典包含价格和频次
        """
        if len(support_prices) == 0:
            return []
        
        merged_levels = []
        
        # 对价格排序
        sorted_prices = np.sort(support_prices)
        current_group = [sorted_prices[0]]
        
        for price in sorted_prices[1:]:
            # 计算与当前组平均值的差距
            group_avg = np.mean(current_group)
            price_diff = abs(price - group_avg) / group_avg
            
            if price_diff <= threshold:
                # 如果差距在阈值内，加入当前组
                current_group.append(price)
            else:
                # 如果差距过大，保存当前组并开始新组
                merged_levels.append({
                    'price': np.mean(current_group),
                    'frequency': len(current_group)
                })
                current_group = [price]
        
        # 处理最后一组
        if current_group:
            merged_levels.append({
                'price': np.mean(current_group),
                'frequency': len(current_group)
            })
        
        return merged_levels

    def find_support_levels(self, 
                          df: pd.DataFrame, 
                          window: int = 20,
                          threshold: float = 0.02,
                          merge_threshold: float = 0.20) -> List[Dict]:
        """
        寻找支撑位并合并
        """
        try:
            prices = df['close'].values
            # 使用自定义函数找出局部最小值
            local_mins = self.find_local_minima(prices, window)
            support_prices = prices[local_mins]
            
            # 对支撑位进行初步筛选
            filtered_supports = []
            for price in support_prices:
                if not any(abs(price - s['price']) / s['price'] < threshold 
                          for s in filtered_supports):
                    filtered_supports.append({
                        'price': price,
                        'frequency': 1
                    })
            
            # 合并接近的支撑位
            merged_levels = self.merge_support_levels(
                np.array([s['price'] for s in filtered_supports]),
                merge_threshold
            )
            
            if merged_levels:
                logger.info(f"找到 {len(merged_levels)} 个支撑位")
            
            return sorted(merged_levels, key=lambda x: x['price'])
            
        except Exception as e:
            logger.error(f"寻找支撑位失败: {str(e)}")
            return []

    def calculate_price_strength(self, 
                               df: pd.DataFrame,
                               support_level: float) -> float:
        """
        计算支撑位强度
        """
        try:
            # 计算价格在支撑位附近停留的次数
            near_support = df['close'].apply(
                lambda x: abs(x - support_level) / support_level < 0.02
            ).sum()
            
            # 计算支撑位强度得分
            strength = near_support / len(df)
            return strength
        except Exception as e:
            logger.error(f"计算支撑位强度失败: {str(e)}")
            return 0.0

    def analyze_all_tokens(self) -> None:
        """
        分析所有代币，并保存两种结果：
        1. 原始分析数据（每次生成新的时间戳文件）
        2. 警报数据（追加到固定文件）
        """
        try:
            analysis_data = []
            analysis_time = datetime.now()
            
            # 获取所有需要处理的文件
            files_to_process = [
                f for f in os.listdir(self.data_folder)
                if f.endswith('.csv') and not f.startswith('support_resistance_') and not f.startswith('price_alerts')
            ]
            
            logger.info(f"开始分析支撑位 - 待处理文件数: {len(files_to_process)}")
            
            # 处理每个代币
            for file_name in files_to_process:
                token_symbol = file_name.replace('.csv', '').split('_')[0]
                df = self.load_token_data(file_name.replace('.csv', ''))
                if df is None:
                    continue
                    
                support_levels = self.find_support_levels(df)
                if not support_levels:
                    continue

                current_price = float(df['close'].iloc[-1])
                
                # 添加到分析数据列表
                for i, level in enumerate(support_levels, 1):
                    distance = ((current_price - level['price']) / level['price']) * 100
                    analysis_data.append({
                        'analysis_time': analysis_time,
                        'token': token_symbol,
                        'current_price': current_price,
                        'support_level': level['price'],
                        'frequency': level['frequency'],
                        'distance_percent': distance,
                        'level_rank': i
                    })
            
            # 生成带时间戳的分析文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_file_path = os.path.join(
                os.path.dirname(self.data_folder),
                f"support_resistance_analysis_{timestamp}.csv"
            )
            
            # 保存分析数据到新文件
            df = pd.DataFrame(analysis_data)
            df.to_csv(analysis_file_path, index=False)
            logger.info(f"分析结果已保存到: {analysis_file_path}")
            
            # 生成警报数据（追加到固定文件）
            self.generate_alert_file(analysis_data)
            
        except Exception as e:
            logger.error(f"分析过程出错: {str(e)}")

    def generate_alert_file(self, analysis_data: List[Dict]) -> None:
        """
        生成警报数据文件（筛选频次>3且价格差距<1%的数据）并追加到固定文件
        """
        try:
            df = pd.DataFrame(analysis_data)
            
            # 筛选符合条件的数据
            alert_df = df[
                (df['frequency'] > 3) & 
                (abs(df['distance_percent']) < 1)
            ].copy()
            
            if not alert_df.empty:
                # 固定的警报文件路径
                alert_file_path = os.path.join(
                    os.path.dirname(self.data_folder),
                    "price_alerts.csv"
                )
                
                # 如果文件不存在，创建新文件并写入表头
                if not os.path.exists(alert_file_path):
                    alert_df.to_csv(alert_file_path, index=False)
                else:
                    # 追加模式，不写入表头
                    alert_df.to_csv(alert_file_path, mode='a', header=False, index=False)
                    
                logger.info(f"警报数据已追加到: {alert_file_path}")
            
        except Exception as e:
            logger.error(f"生成警报数据失败: {str(e)}")

    def generate_alerts(self, 
                       results: Dict[str, Dict],
                       alert_threshold: float = 0.05) -> List[Dict]:
        """
        生成价格接近支撑位的提醒
        """
        alerts = []
        for token, data in results.items():
            current_price = float(data['current_price'])
            
            for support_level in data['support_levels']:
                price_diff = (current_price - float(support_level['price'])) / float(support_level['price'])
                
                if abs(price_diff) < alert_threshold:
                    strength = float(data['support_strengths'][float(support_level['price'])])
                    alerts.append({
                        'token': token,
                        'current_price': current_price,
                        'support_level': float(support_level['price']),
                        'distance': float(price_diff),
                        'strength': strength
                    })
                    
        return sorted(alerts, key=lambda x: abs(x['distance']))

    def check_price_alerts(self, token_symbol: str, current_price: float, 
                          support_levels: List[Dict], threshold: float = 0.01) -> List[Dict]:
        """
        检查价格是否接近支撑位并返回符合条件的支撑位数据
        
        Args:
            token_symbol: 代币符号
            current_price: 当前价格
            support_levels: 支撑位列表
            threshold: 触发阈值（默认1%）
            
        Returns:
            List[Dict]: 符合条件的支撑位列表
        """
        alert_data = []
        
        for level in support_levels:
            # 只处理频次大于3的支撑位
            if level['frequency'] <= 3:
                continue
            
            # 计算价格差距
            price_diff = abs(current_price - level['price']) / level['price']
            
            # 如果价格接近支撑位（1%以内）
            if price_diff < threshold:
                alert_data.append({
                    'token': token_symbol,
                    'current_price': current_price,
                    'support_level': level['price'],
                    'frequency': level['frequency'],
                    'distance_percent': price_diff * 100,
                    'analysis_time': datetime.now()
                })
        
        return alert_data

    def save_price_alerts(self, alerts: List[Dict], output_path: str):
        """
        保存价格警报数据到新文件
        
        Args:
            alerts: 警报数据列表
            output_path: 输出文件路径
        """
        try:
            df = pd.DataFrame(alerts)
            df.to_csv(output_path, index=False)
            logger.info(f"价格警报数据已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存价格警报数据失败: {str(e)}")

    def get_support_level_strength(self, token_symbol: str, support_price: float) -> float:
        """
        获取特定支撑位的强度
        """
        df = self.load_token_data(token_symbol)
        if df is not None:
            return self.calculate_price_strength(df, support_price)
        return 0.0

    def filter_recent_alerts(self) -> None:
        """
        处理最近4小时内的警报数据，去除重复警报
        """
        try:
            # 读取price_alerts.csv
            alerts_file = os.path.join(os.path.dirname(self.data_folder), "price_alerts.csv")
            if not os.path.exists(alerts_file):
                logger.warning("未找到price_alerts.csv文件")
                return
            
            # 读取警报数据
            df = pd.read_csv(alerts_file)
            df['analysis_time'] = pd.to_datetime(df['analysis_time'])
            
            # 获取最新时间
            latest_time = df['analysis_time'].max()
            
            # 获取4小时内的数据
            four_hours = pd.Timedelta(hours=4)
            recent_df = df[df['analysis_time'] >= (latest_time - four_hours)]
            
            if recent_df.empty:
                logger.info("没有找到4小时内的警报数据")
                return
            
            # 创建唯一标识：代币+支撑位
            recent_df['alert_id'] = recent_df.apply(
                lambda x: f"{x['token']}_{x['support_level']:.8f}", 
                axis=1
            )
            
            # 按时间排序，保留每个alert_id的第一次出现
            unique_alerts = recent_df.sort_values('analysis_time').drop_duplicates(
                subset=['alert_id'], 
                keep='first'
            )
            
            # 只保留最新时间点的警报
            latest_alerts = unique_alerts[
                unique_alerts['analysis_time'] == latest_time
            ]
            
            if not latest_alerts.empty:
                # 生成新的文件名（使用最新时间）
                timestamp = latest_time.strftime("%Y%m%d_%H%M%S")
                new_file_path = os.path.join(
                    os.path.dirname(self.data_folder),
                    f"new_alerts_{timestamp}.csv"
                )
                
                # 保存所有原始列（删除临时添加的alert_id列）
                columns_to_save = [
                    'analysis_time', 'token', 'current_price', 
                    'support_level', 'frequency', 'distance_percent', 
                    'level_rank'
                ]
                latest_alerts[columns_to_save].to_csv(new_file_path, index=False)
                
                logger.info(f"新的未重复警报已保存到: {new_file_path}")
                logger.info(f"共发现 {len(latest_alerts)} 个新的未重复警报")
            else:
                logger.info("没有发现新的未重复警报")
            
        except Exception as e:
            logger.error(f"处理警报去重时出错: {str(e)}")

# 添加主函数入口
if __name__ == "__main__":
    # 使用项目的data/token目录
    data_folder = os.path.join(os.getcwd(), 'data', 'token')
    
    # 确保文件夹存在
    if not os.path.exists(data_folder):
        logger.error(f"错误: {data_folder} 文件夹不存在")
        exit(1)
    
    # 检查文件夹是否为空
    if not any(file.endswith('.csv') for file in os.listdir(data_folder)):
        logger.error(f"错误: {data_folder} 文件夹中没有CSV文件")
        exit(1)
    
    logger.info("开始支撑位分析...")
    
    # 创建分析器实例
    analyzer = SupportResistanceAnalyzer(data_folder)
    
    # 分析所有代币
    analyzer.analyze_all_tokens()
    
    # 处理警报去重
    analyzer.filter_recent_alerts() 