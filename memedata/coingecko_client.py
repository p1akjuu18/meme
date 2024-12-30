import requests
import pandas as pd
from datetime import datetime
import os
import time


class CoinGeckoClient:
    def __init__(self, api_key=None):
        self.base_url = "https://pro-api.coingecko.com/api/v3"
        self.api_key = api_key
        self.headers = {
            'x-cg-pro-api-key': api_key
        } if api_key else {}

    def get_solana_tokens(self):
        """
        获取Solana网络上的代币基本信息
        """
        endpoint = "/onchain/tokens/info_recently_updated"
        params = {
            'include': 'network',
            'network': 'solana'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=10
            )
            print(f"请求基本信息URL: {response.url}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求基本信息出错: {e}")
            return None

    def export_to_excel(self, save_dir='data'):
        """
        获取Solana代币数据并导出到Excel
        """
        os.makedirs(save_dir, exist_ok=True)
        
        # 第一步：获取基本信息
        tokens_data = self.get_solana_tokens()
        if not tokens_data or 'data' not in tokens_data:
            print("没有获取到代币基本信息")
            return

        # 准备基本数据列表
        processed_data = []
        addresses = []  # 收集地址用于第二步请求
        
        for token in tokens_data['data']:
            attrs = token.get('attributes', {})
            addr = attrs.get('address')
            if addr:
                addresses.append(addr)
                processed_data.append({
                    '代币名称': attrs.get('name', 'N/A'),
                    '代币符号': attrs.get('symbol', 'N/A'),
                    '合约地址': addr,
                    '描述': attrs.get('description', 'N/A'),
                    'GT评分': attrs.get('gt_score', 0),
                    '更新时间': attrs.get('metadata_updated_at', 'N/A'),
                    'Discord链接': attrs.get('discord_url', 'N/A'),
                    'Telegram': attrs.get('telegram_handle', 'N/A'),
                    'Twitter': attrs.get('twitter_handle', 'N/A'),
                    # 以下字段将在第二步填充
                    '精度': 'N/A',
                    '总供应量': 'N/A',
                    '价格(USD)': 'N/A',
                    '完全稀释估值(USD)': 'N/A',
                    '总锁仓量(USD)': 'N/A',
                    '24h成交量(USD)': 'N/A',
                    '市值(USD)': 'N/A',
                    # 交易池相关字段
                    '5分钟价格变化%': 'N/A',
                    '1小时价格变化%': 'N/A',
                    '6小时价格变化%': 'N/A',
                    '24小时价格变化%': 'N/A',
                    '5分钟买入次数': 'N/A',
                    '5分钟卖出次数': 'N/A',
                    '15分钟买入次数': 'N/A',
                    '15分钟卖出次数': 'N/A',
                    '30分钟买入次数': 'N/A',
                    '30分钟卖出次数': 'N/A',
                    '1小时买入次数': 'N/A',
                    '1小时卖出次数': 'N/A',
                    '24小时买入次数': 'N/A',
                    '24小时卖出次数': 'N/A',
                    '5分钟交易量': 'N/A',
                    '1小时交易量': 'N/A',
                    '6小时交易量': 'N/A'
                })

        print(f"总共获取到 {len(addresses)} 个代币地址")

        # 第二步：获取详细数据
        if addresses:
            batch_size = 30
            for i in range(0, len(addresses), batch_size):
                batch_addresses = addresses[i:i + batch_size]
                endpoint = f"/onchain/networks/solana/tokens/multi/{','.join(batch_addresses)}"
                
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=self.headers,
                        params={'include': 'top_pools'},
                        timeout=10
                    )
                    print(f"请求详细数据URL (批次 {i//batch_size + 1}): {response.url}")
                    response.raise_for_status()
                    detailed_data = response.json()
                    
                    if 'data' in detailed_data:
                        for token in detailed_data['data']:
                            attrs = token.get('attributes', {})
                            relationships = token.get('relationships', {})
                            addr = attrs.get('address')
                            
                            # 先获取top_pools的ID
                            top_pools = relationships.get('top_pools', {}).get('data', [])
                            pool_ids = [pool.get('id') for pool in top_pools]
                            
                            # 在included中查找对应的交易池数据
                            for pool_id in pool_ids:
                                for included in detailed_data.get('included', []):
                                    if included.get('id') == pool_id and included.get('type') == 'pool':
                                        pool_attrs = included.get('attributes', {})
                                        
                                        # 找到对应的记录并更新
                                        for record in processed_data:
                                            if record['合约地址'] == addr:
                                                # 更新代币基本数据
                                                record.update({
                                                    '精度': attrs.get('decimals', 'N/A'),
                                                    '总供应量': attrs.get('total_supply', 'N/A'),
                                                    '价格(USD)': attrs.get('price_usd', 'N/A'),
                                                    '完全稀释估值(USD)': attrs.get('fdv_usd', 'N/A'),
                                                    '总锁仓量(USD)': attrs.get('total_reserve_in_usd', 'N/A'),
                                                    '24h成交量(USD)': attrs.get('volume_usd', {}).get('h24', 'N/A'),
                                                    '市值(USD)': attrs.get('market_cap_usd', 'N/A'),
                                                })
                                                
                                                # 更新交易池数据
                                                price_changes = pool_attrs.get('price_change_percentage', {})
                                                transactions = pool_attrs.get('transactions', {})
                                                volumes = pool_attrs.get('volume_usd', {})
                                                
                                                record.update({
                                                    # 价格变化数据
                                                    '5分钟价格变化%': price_changes.get('m5', 'N/A'),
                                                    '1小时价格变化%': price_changes.get('h1', 'N/A'),
                                                    '6小时价格变化%': price_changes.get('h6', 'N/A'),
                                                    '24小时价格变化%': price_changes.get('h24', 'N/A'),
                                                    # 交易次数数据
                                                    '5分钟买入次数': transactions.get('m5', {}).get('buys', 0),
                                                    '5分钟卖出次数': transactions.get('m5', {}).get('sells', 0),
                                                    '15分钟买入次数': transactions.get('m15', {}).get('buys', 0),
                                                    '15分钟卖出次数': transactions.get('m15', {}).get('sells', 0),
                                                    '30分钟买入次数': transactions.get('m30', {}).get('buys', 0),
                                                    '30分钟卖出次数': transactions.get('m30', {}).get('sells', 0),
                                                    '1小时买入次数': transactions.get('h1', {}).get('buys', 0),
                                                    '1小时卖出次数': transactions.get('h1', {}).get('sells', 0),
                                                    '24小时买入次数': transactions.get('h24', {}).get('buys', 0),
                                                    '24小时卖出次数': transactions.get('h24', {}).get('sells', 0),
                                                    # 交易量数据
                                                    '5分钟交易量': volumes.get('m5', 'N/A'),
                                                    '1小时交易量': volumes.get('h1', 'N/A'),
                                                    '6小时交易量': volumes.get('h6', 'N/A')
                                                })
                                                break
                                        break  # 只使用第一个交易池的数据

                except requests.exceptions.RequestException as e:
                    print(f"请求详细数据出错 (批次 {i//batch_size + 1}): {e}")
                
                time.sleep(1)

        # 创建DataFrame并导出到Excel
        df = pd.DataFrame(processed_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'solana_tokens_detailed_{timestamp}.xlsx'
        full_path = os.path.join(save_dir, filename)
        
        df.to_excel(full_path, index=False, engine='openpyxl')
        print(f"数据已导出到文件: {os.path.abspath(full_path)}")
        return full_path

# 使用示例
if __name__ == "__main__":
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    client = CoinGeckoClient(api_key="CG-W6NCZupELQfrh1irod8sb3cb")
    client.export_to_excel(save_dir=desktop_path)
