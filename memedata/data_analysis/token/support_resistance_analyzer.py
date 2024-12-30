import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import os
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
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
            file_path = os.path.join(self.data_folder, f"{token_symbol}.csv")
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # 按时间戳排序
            df = df.sort_values('timestamp', ascending=True)
            return df
        except Exception as e:
            logger.error(f"加载{token_symbol}数据失败: {str(e)}")
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

    def analyze_all_tokens(self) -> Dict[str, Dict]:
        """
        分析所有代币的支撑位
        """
        results = {}
        for file_name in os.listdir(self.data_folder):
            if not file_name.endswith('.csv'):
                continue
                
            token_symbol = file_name.replace('.csv', '')
            df = self.load_token_data(token_symbol)
            if df is None:
                continue
                
            support_levels = self.find_support_levels(df)
            current_price = df['close'].iloc[-1]
            
            # 计算每个支撑位的强度
            support_strengths = {
                level: self.calculate_price_strength(df, level)
                for level in support_levels
            }
            
            results[token_symbol] = {
                'current_price': current_price,
                'support_levels': support_levels,
                'support_strengths': support_strengths
            }
            
        return results

    def generate_alerts(self, 
                       results: Dict[str, Dict],
                       alert_threshold: float = 0.05) -> List[Dict]:
        """
        生成价格接近支撑位的提醒
        """
        alerts = []
        for token, data in results.items():
            current_price = data['current_price']
            
            for support_level in data['support_levels']:
                price_diff = (current_price - support_level['price']) / support_level['price']
                
                if abs(price_diff) < alert_threshold:
                    strength = data['support_strengths'][support_level['price']]
                    alerts.append({
                        'token': token,
                        'current_price': current_price,
                        'support_level': support_level['price'],
                        'distance': price_diff,
                        'strength': strength
                    })
                    
        return sorted(alerts, key=lambda x: abs(x['distance'])) 

    def save_analysis_results(self, results: Dict[str, Dict], output_path: str) -> None:
        """
        保存分析结果到CSV文件
        """
        try:
            # 准备数据
            analysis_data = []
            for token_symbol, data in results.items():
                current_price = data['current_price']
                for i, level in enumerate(data['support_levels'], 1):
                    distance = ((current_price - level['price']) / level['price']) * 100
                    analysis_data.append({
                        'token': token_symbol,
                        'current_price': current_price,
                        'support_level': level['price'],
                        'frequency': level['frequency'],
                        'distance_percent': distance,
                        'level_rank': i
                    })
            
            # 创建DataFrame并保存
            df = pd.DataFrame(analysis_data)
            df.to_csv(output_path, index=False)
            logger.info(f"分析结果已保存到: {output_path}")
            
        except Exception as e:
            logger.error(f"保存分析结果失败: {str(e)}")

# 添加主函数入口
if __name__ == "__main__":
    # 获取Windows桌面路径
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    # 构建token1文件夹的完整路径
    data_folder = os.path.join(desktop_path, "token")
    
    # 确保文件夹存在
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        print(f"创建文件夹: {data_folder}")
        print("请将CSV数据文件放入此文件夹中")
        exit()
    
    # 检查文件夹是否为空
    if not any(file.endswith('.csv') for file in os.listdir(data_folder)):
        print(f"错误: {data_folder} 文件夹中没有CSV文件")
        print("请将CSV数据文件放入此文件夹中")
        exit()
    
    # 创建分析器实例
    analyzer = SupportResistanceAnalyzer(data_folder)
    
    # 存储所有代币的分析结果
    all_results = {}
    
    # 遍历文件夹中的所有CSV文件
    for file_name in os.listdir(data_folder):
        if not file_name.endswith('.csv'):
            continue
            
        token_symbol = file_name.replace('.csv', '')
        logger.info(f"\n分析代币: {token_symbol}")
        
        # 加载数据
        df = analyzer.load_token_data(token_symbol)
        if df is None:
            continue
        
        # 获取最新的价格（确保数据已按时间排序）
        current_price = df.iloc[-1]['close']
        
        # 计算支撑位
        support_levels = analyzer.find_support_levels(df)
        
        # 存储结果
        all_results[token_symbol] = {
            'current_price': current_price,
            'support_levels': support_levels
        }
        
        # 打印结果
        print(f"\n{'='*50}")
        print(f"代币: {token_symbol}")
        print(f"当前价格: {current_price:.8f}")
        print(f"\n发现的支撑位:")
        
        for i, level in enumerate(support_levels, 1):
            distance = ((current_price - level['price']) / level['price']) * 100
            print(f"{i}. 价格: {level['price']:.8f} (频次: {level['frequency']}, 距离当前价格: {distance:.2f}%)")
        
        print(f"{'='*50}\n")
    
    # 保存结果到CSV文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(desktop_path, f'support_analysis_{timestamp}.csv')
    analyzer.save_analysis_results(all_results, output_file) 