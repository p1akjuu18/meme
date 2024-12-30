import pandas as pd
import numpy as np
from typing import List, Dict, Union, Optional
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdvancedDataProcessor:
    """
    高级数据处理类，用于处理复杂的数据分析任务
    """
    
    def __init__(self):
        self.data = None
        
    def load_data(self, data: Union[pd.DataFrame, str]) -> None:
        """
        加载数据，支持DataFrame或文件路径
        
        Args:
            data: DataFrame对象或数据文件路径
        """
        try:
            if isinstance(data, pd.DataFrame):
                self.data = data
            elif isinstance(data, str):
                self.data = pd.read_csv(data)
            logger.info("数据加载成功")
        except Exception as e:
            logger.error(f"数据加载失败: {str(e)}")
            raise
            
    def process_time_series(self, 
                          column: str,
                          window_size: int = 24,
                          methods: List[str] = ['mean', 'std']) -> pd.DataFrame:
        """
        时间序列数据处理
        
        Args:
            column: 要处理的列名
            window_size: 滑动窗口大小
            methods: 统计方法列表
            
        Returns:
            处理后的DataFrame
        """
        if self.data is None:
            raise ValueError("请先加载数据")
            
        result = pd.DataFrame()
        for method in methods:
            try:
                result[f'{column}_{method}_{window_size}h'] = (
                    self.data[column].rolling(window=window_size).agg(method)
                )
            except Exception as e:
                logger.error(f"处理{method}方法时出错: {str(e)}")
                
        return result
    
    def detect_anomalies(self,
                        column: str,
                        threshold: float = 3.0) -> pd.Series:
        """
        异常检测
        
        Args:
            column: 要检测的列名
            threshold: 标准差倍数阈值
            
        Returns:
            布尔序列，True表示异常值
        """
        if self.data is None:
            raise ValueError("请先加载数据")
            
        try:
            series = self.data[column]
            mean = series.mean()
            std = series.std()
            return abs(series - mean) > (threshold * std)
        except Exception as e:
            logger.error(f"异常检测失败: {str(e)}")
            raise
            
    def calculate_metrics(self, 
                         target_column: str,
                         feature_columns: List[str]) -> Dict[str, float]:
        """
        计算统计指标
        
        Args:
            target_column: 目标列名
            feature_columns: 特征列名列表
            
        Returns:
            包含各种统计指标的字典
        """
        if self.data is None:
            raise ValueError("请先加载数据")
            
        metrics = {}
        try:
            # 基本统计量
            metrics['mean'] = self.data[target_column].mean()
            metrics['median'] = self.data[target_column].median()
            metrics['std'] = self.data[target_column].std()
            
            # 相关性分析
            for feature in feature_columns:
                correlation = self.data[target_column].corr(self.data[feature])
                metrics[f'correlation_{feature}'] = correlation
                
            return metrics
        except Exception as e:
            logger.error(f"指标计算失败: {str(e)}")
            raise 