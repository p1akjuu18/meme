from pycoingecko import CoinGeckoAPI
import pandas as pd
import os
import time
import requests

class TokenInfoFetcher:
    def __init__(self):
        self.cg = CoinGeckoAPI(api_key="CG-dJ6UcnVr8yvqw5Cvm8CywKvD")

    def get_token_info(self, network, address):
        """
        获取代币的详细信息
        """
        try:
            headers = {
                'x-cg-pro-api-key': "CG-dJ6UcnVr8yvqw5Cvm8CywKvD"
            }
            
            base_url = "https://pro-api.coingecko.com/api/v3"
            endpoint = f"{base_url}/onchain/networks/{network}/tokens/{address}/info"
            
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and 'attributes' in data['data']:
                attributes = data['data']['attributes']
                return {
                    'description': attributes.get('description', ''),
                    'websites': attributes.get('websites', []),
                    'twitter_handle': attributes.get('twitter_handle', ''),
                    'telegram_handle': attributes.get('telegram_handle', '')
                }
            return None
            
        except Exception as e:
            print(f"获取代币信息时出错: {str(e)}")
            return None

def clean_text(text, max_length=32000):
    """
    清理文本数据，移除特殊字符并限制长度
    """
    if not isinstance(text, str):
        return ''
    # 移除可能导致Excel保存问题的字符
    text = text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    # 限制文本长度
    return text[:max_length] if len(text) > max_length else text

def clean_list(lst, max_length=1000):
    """
    清理列表数据，将其转换为字符串并限制长度
    """
    if not lst:
        return ''
    text = ', '.join(str(item) for item in lst if item)
    return clean_text(text, max_length)

def process_token_info(start_index=0, batch_size=10):
    # 获取桌面路径
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    output_excel_path = os.path.join(desktop_path, 'token_info_basic.xlsx')
    
    try:
        # 读取Excel文件
        excel_path = os.path.join(desktop_path, 'token_query_results_all_20250108_205910_cleaned.xlsx')
        df = pd.read_excel(excel_path)
        
        print("Excel文件中的列名:", df.columns.tolist())
        print(f"将从第 {start_index} 个代币开始处理...")
        
        fetcher = TokenInfoFetcher()
        
        # 如果输出文件已存在，读取已有数据
        if os.path.exists(output_excel_path):
            existing_df = pd.read_excel(output_excel_path)
            processed_indices = existing_df.index.tolist()
        else:
            df['description'] = ''
            df['websites'] = ''
            df['twitter_handle'] = ''
            df['telegram_handle'] = ''
            processed_indices = []
        
        # 用于记录上次保存的时间
        last_save_time = time.time()
        modified = False
        
        # 遍历每个代币，从指定索引开始
        for index, row in df.iloc[start_index:].iterrows():
            if index in processed_indices:
                continue
                
            try:
                token_address = row['代币地址']
                symbol = row['符号']
                
                if pd.isna(token_address) or pd.isna(symbol):
                    continue
                    
                print(f"正在获取 {symbol} ({index + 1}/{len(df)}) 的基本信息...")
                
                # 获取代币额外信息
                token_info = fetcher.get_token_info('solana', token_address)
                if token_info:
                    # 清理并保存数据
                    df.at[index, 'description'] = clean_text(token_info['description'])
                    df.at[index, 'websites'] = clean_list(token_info['websites'])
                    df.at[index, 'twitter_handle'] = clean_text(token_info['twitter_handle'])
                    df.at[index, 'telegram_handle'] = clean_text(token_info['telegram_handle'])
                    modified = True
                    print(f"已获取并清理 {symbol} 的基本信息")
                else:
                    print(f"无法获取 {symbol} 的基本信息")
                
                # 每处理batch_size条数据或者经过60秒就保存一次
                current_time = time.time()
                if modified and (index % batch_size == 0 or current_time - last_save_time >= 60):
                    try:
                        # 创建临时文件
                        temp_file = output_excel_path.replace('.xlsx', '_temp.xlsx')
                        df.to_excel(temp_file, index=False)
                        # 如果临时文件创建成功，则替换原文件
                        if os.path.exists(output_excel_path):
                            os.remove(output_excel_path)
                        os.rename(temp_file, output_excel_path)
                        print(f"已保存当前进度到: {output_excel_path}")
                        last_save_time = current_time
                        modified = False
                    except Exception as save_error:
                        print(f"保存文件时出错: {str(save_error)}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"处理 {symbol} 时出错: {str(e)}")
                continue
        
        # 最后保存一次
        if modified:
            try:
                temp_file = output_excel_path.replace('.xlsx', '_temp.xlsx')
                df.to_excel(temp_file, index=False)
                if os.path.exists(output_excel_path):
                    os.remove(output_excel_path)
                os.rename(temp_file, output_excel_path)
                print("最终数据已保存")
            except Exception as final_save_error:
                print(f"最终保存文件时出错: {str(final_save_error)}")
        
        print("所有数据处理完成！")
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")

if __name__ == "__main__":
    process_token_info(start_index=0) 