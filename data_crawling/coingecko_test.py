import requests
import json
import pandas as pd
import os
from time import sleep
import signal
import sys
import time
from datetime import datetime

# CoinGecko API配置
COINGECKO_API_KEY = "CG-dJ6UcnVr8yvqw5Cvm8CywKvD"

def get_latest_processed_links():
    """获取最新的processed_links文件"""
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"错误：未找到数据文件夹: {data_dir}")
        return None

    # 查找processed_links_开头的文件
    links_files = [f for f in os.listdir(data_dir) if f.startswith('processed_links_') and f.endswith('.xlsx')]
    if not links_files:
        print("错误：未找到processed_links文件")
        return None

    # 按文件名排序（因为文件名包含时间戳）
    latest_file = sorted(links_files)[-1]
    return os.path.join(data_dir, latest_file)

def monitor_tokens():
    """从最新的processed_links文件读取代币地址"""
    latest_file = get_latest_processed_links()
    if not latest_file:
        return []
        
    print(f"正在读取文件: {latest_file}")
    df = pd.read_excel(latest_file)
    addresses = df['Token Address'].tolist()
    return addresses

def save_results_to_excel(results, timestamp=None):
    """统一的保存结果函数"""
    if not timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 确保data目录存在
    if not os.path.exists('data'):
        os.makedirs('data')
        
    # 统一的输出文件名格式
    output_file = os.path.join('data', f'token_query_results_all_{timestamp}.xlsx')
    
    # 保存结果
    if results:
        df_results = pd.DataFrame(results)
        
        # 处理代币地址列，删除solana_前缀
        if '代币地址' in df_results.columns:
            df_results['代币地址'] = df_results['代币地址'].apply(lambda x: x.replace('solana_', '') if isinstance(x, str) else x)
        
        df_results.to_excel(output_file, index=False)
        print(f"\n查询结果已保存到: {output_file}")
        print(f"总记录数: {len(results)}")
    else:
        print("没有查询结果可保存")

class CoinGeckoTest:
    def __init__(self, api_key=None):
        self.base_url = "https://pro-api.coingecko.com/api/v3"
        self.api_key = api_key or COINGECKO_API_KEY
        self.headers = {
            'x-cg-pro-api-key': self.api_key
        }
        self.running = True
        self.previous_data = {}  # 存储上一次的数据
        signal.signal(signal.SIGINT, self.signal_handler)
        self.results = []  # 用于存储所有查询结果

    def signal_handler(self, signum, frame):
        """
        处理终止信号
        """
        print("\n\n收到终止信号，正在安全退出程序...")
        self.running = False

    def get_token_info(self, address, network='solana'):
        """
        通过代币地址获取代币信息
        
        参数:
            address: 代币合约地址 (例如: DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263)
            network: 网络名称，默认为'solana'
        """
        endpoint = f"/onchain/networks/{network}/tokens/{address}"
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params={'include': 'top_pools'}  # 包含交易池信息
            )
            print(f"\n查询代币地址: {address}")
            print(f"网络: {network}")
            print(f"URL: {response.url}")
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'attributes' in data['data']:
                    attrs = data['data']['attributes']
                    
                    # 扩展保存的数据
                    result_row = {
                        '代币地址': address,
                        # 基本信息
                        '名称': attrs.get('name'),
                        '符号': attrs.get('symbol'),
                        '精度': attrs.get('decimals'),
                        # 价格信息
                        '价格(USD)': attrs.get('price_usd'),
                        '24h成交量(USD)': attrs.get('volume_usd', {}).get('h24'),
                        '总供应量': attrs.get('total_supply'),
                        '总锁仓量(USD)': attrs.get('total_reserve_in_usd'),
                        '完全稀释估值(USD)': attrs.get('fdv_usd'),
                        '市值(USD)': attrs.get('market_cap_usd'),
                        '查询时间': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # 添加交易池信息
                    if 'included' in data:
                        pool_count = 0
                        for included in data['included']:
                            if included.get('type') == 'pool':
                                pool_count += 1
                                pool_attrs = included.get('attributes', {})
                                pool_prefix = f'交易池{pool_count}_'
                                
                                # 添加池子基本信息
                                result_row.update({
                                    f'{pool_prefix}名称': pool_attrs.get('name'),
                                    f'{pool_prefix}地址': pool_attrs.get('address'),
                                    f'{pool_prefix}创建时间': pool_attrs.get('pool_created_at'),
                                })
                                
                                # 添加价格变化信息
                                price_changes = pool_attrs.get('price_change_percentage', {})
                                result_row.update({
                                    f'{pool_prefix}价格变化_5分钟': price_changes.get('m5'),
                                    f'{pool_prefix}价格变化_1小时': price_changes.get('h1'),
                                    f'{pool_prefix}价格变化_6小时': price_changes.get('h6'),
                                    f'{pool_prefix}价格变化_24小时': price_changes.get('h24')
                                })
                                
                                # 添加交易量信息
                                volumes = pool_attrs.get('volume_usd', {})
                                result_row.update({
                                    f'{pool_prefix}交易量_5分钟': volumes.get('m5'),
                                    f'{pool_prefix}交易量_1小时': volumes.get('h1'),
                                    f'{pool_prefix}交易量_6小时': volumes.get('h6'),
                                    f'{pool_prefix}交易量_24小时': volumes.get('h24')
                                })
                                
                                # 添加交易次数信息
                                transactions = pool_attrs.get('transactions', {})
                                for period in ['m5', 'm15', 'm30', 'h1', 'h24']:
                                    period_data = transactions.get(period, {})
                                    result_row.update({
                                        f'{pool_prefix}交易次数_{period}_买入': period_data.get('buys', 0),
                                        f'{pool_prefix}交易次数_{period}_卖出': period_data.get('sells', 0)
                                    })
                    
                    # 添加到结果列表
                    self.results.append(result_row)
                    
                    # 基本信息
                    token_info = {
                        '基本信息': {
                            '名称': attrs.get('name'),
                            '符号': attrs.get('symbol'),
                            '合约地址': attrs.get('address'),
                            '精度': attrs.get('decimals')
                        },
                        '价格信息': {
                            '价格(USD)': attrs.get('price_usd'),
                            '24h成交量(USD)': attrs.get('volume_usd', {}).get('h24'),
                            '总供应量': attrs.get('total_supply'),
                            '总锁仓量(USD)': attrs.get('total_reserve_in_usd'),
                            '完全稀释估值(USD)': attrs.get('fdv_usd'),
                            '市值(USD)': attrs.get('market_cap_usd')
                        }
                    }

                    # 获取交易池信息
                    if 'included' in data:
                        pools_info = []
                        for included in data['included']:
                            if included.get('type') == 'pool':
                                pool_attrs = included.get('attributes', {})
                                pool_info = {
                                    '池子名称': pool_attrs.get('name'),
                                    '池子地址': pool_attrs.get('address'),
                                    '创建时间': pool_attrs.get('pool_created_at'),
                                    '价格变化': {
                                        '5分钟': pool_attrs.get('price_change_percentage', {}).get('m5'),
                                        '1小时': pool_attrs.get('price_change_percentage', {}).get('h1'),
                                        '6小时': pool_attrs.get('price_change_percentage', {}).get('h6'),
                                        '24小时': pool_attrs.get('price_change_percentage', {}).get('h24')
                                    },
                                    '交易量': {
                                        '5分钟': pool_attrs.get('volume_usd', {}).get('m5'),
                                        '1小时': pool_attrs.get('volume_usd', {}).get('h1'),
                                        '6小时': pool_attrs.get('volume_usd', {}).get('h6'),
                                        '24小时': pool_attrs.get('volume_usd', {}).get('h24')
                                    },
                                    '交易次数': {
                                        '5分钟': {
                                            '买入': pool_attrs.get('transactions', {}).get('m5', {}).get('buys', 0),
                                            '卖出': pool_attrs.get('transactions', {}).get('m5', {}).get('sells', 0)
                                        },
                                        '15分钟': {
                                            '买入': pool_attrs.get('transactions', {}).get('m15', {}).get('buys', 0),
                                            '卖出': pool_attrs.get('transactions', {}).get('m15', {}).get('sells', 0)
                                        },
                                        '30分钟': {
                                            '买入': pool_attrs.get('transactions', {}).get('m30', {}).get('buys', 0),
                                            '卖出': pool_attrs.get('transactions', {}).get('m30', {}).get('sells', 0)
                                        },
                                        '1小时': {
                                            '买入': pool_attrs.get('transactions', {}).get('h1', {}).get('buys', 0),
                                            '卖出': pool_attrs.get('transactions', {}).get('h1', {}).get('sells', 0)
                                        },
                                        '24小时': {
                                            '买入': pool_attrs.get('transactions', {}).get('h24', {}).get('buys', 0),
                                            '卖出': pool_attrs.get('transactions', {}).get('h24', {}).get('sells', 0)
                                        }
                                    }
                                }
                                pools_info.append(pool_info)
                        
                        token_info['交易池信息'] = pools_info

                    print("\n代币详细信息:")
                    print(json.dumps(token_info, indent=2, ensure_ascii=False))
                    return data
                else:
                    print("数据格式错误")
                    return None
            else:
                print(f"错误信息: {response.text}")
                return None
        except Exception as e:
            print(f"请求出错: {e}")
            return None

    def batch_get_tokens_info(self, addresses):
        """
        批量获取代币信息（最多30个地址）
        """
        if len(addresses) > 30:
            print("警告：每次最多只能查询30个地址")
            addresses = addresses[:30]
        
        addresses_str = ','.join(addresses)
        endpoint = f"/onchain/networks/solana/tokens/multi/{addresses_str}"
        
        try:
            print(f"正在发送API请求...")  # 添加调试信息
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params={'include': 'top_pools'}
            )
            print(f"API响应状态码: {response.status_code}")  # 添加调试信息
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"错误信息: {response.text}")
                return None
        except Exception as e:
            print(f"请求出错: {e}")
            return None

    def batch_query_from_excel(self, file_name):
        """从Excel文件读取代币地址并批量查询"""
        try:
            desktop_path = os.path.expanduser("~/Desktop")
            input_file_path = os.path.join(desktop_path, file_name)
            
            # 读取Excel文件，修改为读取第一列（索引为0）
            df = pd.read_excel(input_file_path)
            addresses = df.iloc[:, 0].tolist()
            
            print(f"\n成功读取到 {len(addresses)} 个代币地址")
            
            # 按30个地址一组进行批量查询
            for i in range(0, len(addresses), 30):
                if not self.running:
                    print("程序已终止")
                    break
                    
                batch_addresses = addresses[i:i+30]
                print(f"\n正在查询第 {i+1}-{min(i+30, len(addresses))} 个代币...")
                
                data = self.batch_get_tokens_info(batch_addresses)
                if data and 'data' in data:
                    for token_data in data['data']:
                        attrs = token_data.get('attributes', {})
                        address = token_data.get('id')
                        
                        # 构建结果数据
                        result_row = {
                            '代币地址': address,
                            '名称': attrs.get('name'),
                            '符号': attrs.get('symbol'),
                            '精度': attrs.get('decimals'),
                            '价格(USD)': attrs.get('price_usd'),
                            '24h成交量(USD)': attrs.get('volume_usd', {}).get('h24'),
                            '总供应量': attrs.get('total_supply'),
                            '总锁仓量(USD)': attrs.get('total_reserve_in_usd'),
                            '完全稀释估值(USD)': attrs.get('fdv_usd'),
                            '市值(USD)': attrs.get('market_cap_usd'),
                            '查询时间': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 添加交易池信息
                        if 'included' in data:
                            for included in data['included']:
                                if included.get('type') == 'pool' and included.get('relationships', {}).get('base_token', {}).get('data', {}).get('id') == address:
                                    pool_attrs = included.get('attributes', {})
                                    pool_prefix = '交易池_'
                                    
                                    result_row.update({
                                        f'{pool_prefix}名称': pool_attrs.get('name'),
                                        f'{pool_prefix}地址': pool_attrs.get('address'),
                                        f'{pool_prefix}创建时间': pool_attrs.get('pool_created_at'),
                                        f'{pool_prefix}价格变化_5分钟': pool_attrs.get('price_change_percentage', {}).get('m5'),
                                        f'{pool_prefix}价格变化_1小时': pool_attrs.get('price_change_percentage', {}).get('h1'),
                                        f'{pool_prefix}价格变化_6小时': pool_attrs.get('price_change_percentage', {}).get('h6'),
                                        f'{pool_prefix}价格变化_24小时': pool_attrs.get('price_change_percentage', {}).get('h24'),
                                        f'{pool_prefix}交易量_5分钟': pool_attrs.get('volume_usd', {}).get('m5'),
                                        f'{pool_prefix}交易量_1小时': pool_attrs.get('volume_usd', {}).get('h1'),
                                        f'{pool_prefix}交易量_6小时': pool_attrs.get('volume_usd', {}).get('h6'),
                                        f'{pool_prefix}交易量_24小时': pool_attrs.get('volume_usd', {}).get('h24'),
                                        f'{pool_prefix}交易次数_5分钟_买入': pool_attrs.get('transactions', {}).get('m5', {}).get('buys', 0),
                                        f'{pool_prefix}交易次数_5分钟_卖出': pool_attrs.get('transactions', {}).get('m5', {}).get('sells', 0),
                                        f'{pool_prefix}交易次数_15分钟_买入': pool_attrs.get('transactions', {}).get('m15', {}).get('buys', 0),
                                        f'{pool_prefix}交易次数_15分钟_卖出': pool_attrs.get('transactions', {}).get('m15', {}).get('sells', 0),
                                        f'{pool_prefix}交易次数_30分钟_买入': pool_attrs.get('transactions', {}).get('m30', {}).get('buys', 0),
                                        f'{pool_prefix}交易次数_30分钟_卖出': pool_attrs.get('transactions', {}).get('m30', {}).get('sells', 0),
                                        f'{pool_prefix}交易次数_1小时_买入': pool_attrs.get('transactions', {}).get('h1', {}).get('buys', 0),
                                        f'{pool_prefix}交易次数_1小时_卖出': pool_attrs.get('transactions', {}).get('h1', {}).get('sells', 0),
                                        f'{pool_prefix}交易次数_24小时_买入': pool_attrs.get('transactions', {}).get('h24', {}).get('buys', 0),
                                        f'{pool_prefix}交易次数_24小时_卖出': pool_attrs.get('transactions', {}).get('h24', {}).get('sells', 0)
                                    })
                        
                        self.results.append(result_row)
                
                sleep(1)  # 添加延时避免请求过快
            
            # 使用统一的保存函数保存结果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_results_to_excel(self.results, timestamp)
            
        except Exception as e:
            print(f"处理过程中出错: {e}")
            return None

    def compare_volume_changes(self, current_data):
        """
        比较当前数据和上一次数据的成交量变化
        """
        significant_changes = []
        
        for token_data in current_data.get('data', []):
            attrs = token_data.get('attributes', {})
            token_id = token_data.get('id')
            current_volume = attrs.get('volume_usd', {}).get('m5', 0) or 0  # 5分钟成交量
            
            if token_id in self.previous_data:
                previous_volume = self.previous_data[token_id].get('volume', 0)
                if previous_volume > 0:  # 避免除以零
                    volume_change = ((current_volume - previous_volume) / previous_volume) * 100
                    if volume_change >= 100:  # 成交量增加100%以上
                        significant_changes.append({
                            '名称': attrs.get('name'),
                            '符号': attrs.get('symbol'),
                            '地址': token_id,
                            '上次成交量': previous_volume,
                            '当前成交量': current_volume,
                            '增长百分比': f"{volume_change:.2f}%"
                        })
            
            # 更新存储的数据
            self.previous_data[token_id] = {
                'volume': current_volume
            }
        
        return significant_changes

    def process_token_data(self, data, current_time):
        """处理单个代币的数据"""
        if 'data' in data:
            for token_data in data['data']:
                attrs = token_data.get('attributes', {})
                address = token_data.get('id')
                
                # 构建结果数据
                result_row = {
                    '代币地址': address,
                    '名称': attrs.get('name'),
                    '符号': attrs.get('symbol'),
                    '精度': attrs.get('decimals'),
                    '价格(USD)': attrs.get('price_usd'),
                    '24h成交量(USD)': attrs.get('volume_usd', {}).get('h24'),
                    '总供应量': attrs.get('total_supply'),
                    '总锁仓量(USD)': attrs.get('total_reserve_in_usd'),
                    '完全稀释估值(USD)': attrs.get('fdv_usd'),
                    '市值(USD)': attrs.get('market_cap_usd'),
                    '查询时间': current_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 添加交易池信息
                if 'included' in data:
                    for included in data['included']:
                        if included.get('type') == 'pool' and included.get('relationships', {}).get('base_token', {}).get('data', {}).get('id') == address:
                            pool_attrs = included.get('attributes', {})
                            pool_prefix = '交易池_'
                            
                            # 处理创建时间的时区转换
                            created_at = pool_attrs.get('pool_created_at')
                            if created_at:
                                try:
                                    # 将字符串转换为datetime对象，假设输入是UTC时间
                                    utc_time = pd.to_datetime(created_at)
                                    # 转换到UTC+8
                                    local_time = utc_time + pd.Timedelta(hours=8)
                                    # 转换回字符串格式
                                    created_at = local_time.strftime('%Y-%m-%d %H:%M:%S')
                                except Exception as e:
                                    print(f"时间转换错误: {e}")
                            
                            result_row.update({
                                f'{pool_prefix}名称': pool_attrs.get('name'),
                                f'{pool_prefix}地址': pool_attrs.get('address'),
                                f'{pool_prefix}创建时间': created_at,  # 使用转换后的时间
                                f'{pool_prefix}价格变化_5分钟': pool_attrs.get('price_change_percentage', {}).get('m5'),
                                f'{pool_prefix}价格变化_1小时': pool_attrs.get('price_change_percentage', {}).get('h1'),
                                f'{pool_prefix}价格变化_6小时': pool_attrs.get('price_change_percentage', {}).get('h6'),
                                f'{pool_prefix}价格变化_24小时': pool_attrs.get('price_change_percentage', {}).get('h24'),
                                f'{pool_prefix}交易量_5分钟': pool_attrs.get('volume_usd', {}).get('m5'),
                                f'{pool_prefix}交易量_1小时': pool_attrs.get('volume_usd', {}).get('h1'),
                                f'{pool_prefix}交易量_6小时': pool_attrs.get('volume_usd', {}).get('h6'),
                                f'{pool_prefix}交易量_24小时': pool_attrs.get('volume_usd', {}).get('h24'),
                                f'{pool_prefix}交易次数_5分钟_买入': pool_attrs.get('transactions', {}).get('m5', {}).get('buys', 0),
                                f'{pool_prefix}交易次数_5分钟_卖出': pool_attrs.get('transactions', {}).get('m5', {}).get('sells', 0),
                                f'{pool_prefix}交易次数_15分钟_买入': pool_attrs.get('transactions', {}).get('m15', {}).get('buys', 0),
                                f'{pool_prefix}交易次数_15分钟_卖出': pool_attrs.get('transactions', {}).get('m15', {}).get('sells', 0),
                                f'{pool_prefix}交易次数_30分钟_买入': pool_attrs.get('transactions', {}).get('m30', {}).get('buys', 0),
                                f'{pool_prefix}交易次数_30分钟_卖出': pool_attrs.get('transactions', {}).get('m30', {}).get('sells', 0),
                                f'{pool_prefix}交易次数_1小时_买入': pool_attrs.get('transactions', {}).get('h1', {}).get('buys', 0),
                                f'{pool_prefix}交易次数_1小时_卖出': pool_attrs.get('transactions', {}).get('h1', {}).get('sells', 0),
                                f'{pool_prefix}交易次数_24小时_买入': pool_attrs.get('transactions', {}).get('h24', {}).get('buys', 0),
                                f'{pool_prefix}交易次数_24小时_卖出': pool_attrs.get('transactions', {}).get('h24', {}).get('sells', 0)
                            })
                
                # 将处理后的数据添加到结果列表中
                self.results.append(result_row)
        return self.results

    def batch_query_from_latest(self):
        """从最新的processed_links文件读取代币地址并批量查询"""
        try:
            # 获取最新文件路径
            input_file = get_latest_processed_links()
            if not input_file:
                print("未找到processed_links文件，无法继续查询")
                return
                
            # 读取Excel文件
            df = pd.read_excel(input_file)
            addresses = df['Token Address'].tolist()
            
            print(f"\n成功读取到 {len(addresses)} 个代币地址")
            
            # 按30个地址一组进行批量查询
            for i in range(0, len(addresses), 30):
                batch = addresses[i:i+30]
                print(f"\n正在查询第 {i+1} 到 {i+len(batch)} 个地址...")
                
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        # 获取数据
                        data = self.batch_get_tokens_info(batch)
                        if data:
                            current_time = datetime.now()
                            self.process_token_data(data, current_time)
                        break  # 如果成功则跳出重试循环
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = 5 * retry_count  # 递增等待时间：5秒、10秒、15秒
                            print(f"查询出错: {e}")
                            print(f"等待{wait_time}秒后进行第{retry_count + 1}次重试...")
                            time.sleep(wait_time)
                        else:
                            print(f"已重试{max_retries}次仍然失败，跳过当前批次: {e}")
            
            # 使用统一的保存函数保存结果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_results_to_excel(self.results, timestamp)
            
        except Exception as e:
            print(f"批量查询出错: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # 创建CoinGecko客户端实例（如果有API密钥，请在这里传入）
    client = CoinGeckoTest()
    # 从最新的processed_links文件读取并查询
    client.batch_query_from_latest()