import os
import pandas as pd
from support_resistance_analyzer import SupportResistanceAnalyzer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_support_levels(token_folder: str):
    """
    打印所有代币的支撑位信息
    """
    try:
        # 初始化分析器
        analyzer = SupportResistanceAnalyzer(token_folder)
        
        # 遍历文件夹中的所有CSV文件
        for file_name in os.listdir(token_folder):
            if not file_name.endswith('.csv'):
                continue
                
            token_symbol = file_name.replace('.csv', '')
            logger.info(f"\n分析代币: {token_symbol}")
            
            # 加载数据
            df = analyzer.load_token_data(token_symbol)
            if df is None:
                continue
            
            # 获取当前价格
            current_price = df['close'].iloc[-1]
            
            # 计算支撑位
            support_levels = analyzer.find_support_levels(df)
            
            # 打印结果
            print(f"\n{'='*50}")
            print(f"代币: {token_symbol}")
            print(f"当前价格: {current_price:.8f}")
            print(f"\n发现的支撑位:")
            
            for i, level in enumerate(support_levels, 1):
                # 计算与当前价格的距离（百分比）
                distance = ((current_price - level) / level) * 100
                print(f"{i}. 价格: {level:.8f} (距当前价格: {distance:.2f}%)")
            
            print(f"{'='*50}\n")
            
    except Exception as e:
        logger.error(f"分析过程中出错: {str(e)}")

if __name__ == "__main__":
    # 指定token数据文件夹路径
    token_folder = "token1"  # 请根据实际路径修改
    print_support_levels(token_folder) 