from pycoingecko import CoinGeckoAPI
import pandas as pd
import os
import time
import requests
from openai import OpenAI

class TokenInfoFetcher:
    def __init__(self):
        self.cg = CoinGeckoAPI(api_key="CG-hxvheyhm7MautHmckogL3zQJ")
        self.deepseek_client = OpenAI(
            api_key="sk-52a10f8c7d0b402e99b799fd2389678f",
            base_url="https://api.deepseek.com"
        )

    def get_token_info(self, network, address):
        try:
            headers = {
                'x-cg-pro-api-key': "CG-hxvheyhm7MautHmckogL3zQJ"
            }
            
            base_url = "https://pro-api.coingecko.com/api/v3"
            endpoint = f"{base_url}/onchain/networks/{network}/tokens/{address}/info"
            
            response = requests.get(endpoint, headers=headers)
            
            if response.status_code != 200:
                return None
                
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

    def translate_to_chinese(self, text):
        if not text or text.strip() == '':
            return ''
            
        try:
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的翻译助手，请将以下英文文本翻译成中文："},
                    {"role": "user", "content": text}
                ],
                stream=False
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"翻译过程中出错: {str(e)}")
            return text

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
    data_dir = os.path.join(os.getcwd(), 'data')
    
    filtered_files = [f for f in os.listdir(data_dir) if f.startswith('token_query_results_filtered_')]
    if not filtered_files:
        print("未找到token_query_results_filtered_开头的文件")
        return
        
    latest_file = sorted(filtered_files)[-1]
    input_file_path = os.path.join(data_dir, latest_file)
    current_time = time.strftime('%Y%m%d_%H%M%S')
    output_excel_path = os.path.join(data_dir, f'token_info_basic_{current_time}.xlsx')
    
    try:
        df = pd.read_excel(input_file_path)
        print(f"开始处理，总代币数: {len(df)}")
        
        already_processed_count = 0
        invalid_data_count = 0
        processed_count = 0
        
        fetcher = TokenInfoFetcher()
        
        if os.path.exists(output_excel_path):
            existing_df = pd.read_excel(output_excel_path)
            processed_indices = existing_df.index.tolist()
        else:
            df['description'] = ''
            df['websites'] = ''
            df['twitter_handle'] = ''
            df['telegram_handle'] = ''
            processed_indices = []
        
        last_save_time = time.time()
        modified = False
        
        for index, row in df.iloc[start_index:].iterrows():
            if index in processed_indices:
                already_processed_count += 1
                continue
                
            try:
                token_address = row['代币地址']
                symbol = row['符号']
                
                if (symbol == 'STORAGENT' and 
                    token_address == 'CofiHxizezmiQV1r85eV4Midefb6BahAyVeQQQxVpump'):
                    continue
                
                if pd.isna(token_address) or pd.isna(symbol):
                    invalid_data_count += 1
                    continue
                    
                processed_count += 1
                print(f"正在处理: {symbol} ({processed_count}/{len(df)})")
                
                token_info = fetcher.get_token_info('solana', token_address)
                
                if token_info:
                    description = token_info['description']
                    translated_description = fetcher.translate_to_chinese(description) if description else ''
                    
                    df.at[index, 'description'] = clean_text(translated_description)
                    df.at[index, 'websites'] = clean_list(token_info['websites'])
                    df.at[index, 'twitter_handle'] = clean_text(token_info['twitter_handle'])
                    df.at[index, 'telegram_handle'] = clean_text(token_info['telegram_handle'])
                    modified = True
                
                current_time = time.time()
                if modified and (processed_count % batch_size == 0 or current_time - last_save_time >= 60):
                    temp_file = output_excel_path.replace('.xlsx', '_temp.xlsx')
                    df.to_excel(temp_file, index=False)
                    if os.path.exists(output_excel_path):
                        os.remove(output_excel_path)
                    os.rename(temp_file, output_excel_path)
                    last_save_time = current_time
                    modified = False
                    print(f"已保存进度 ({processed_count}/{len(df)})")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"处理 {symbol} 时出错: {str(e)}")
                continue
        
        if modified:
            temp_file = output_excel_path.replace('.xlsx', '_temp.xlsx')
            df.to_excel(temp_file, index=False)
            if os.path.exists(output_excel_path):
                os.remove(output_excel_path)
            os.rename(temp_file, output_excel_path)
        
        print("\n处理完成:")
        print(f"总记录数: {len(df)}")
        print(f"成功处理: {processed_count} 条")
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")

if __name__ == "__main__":
    process_token_info(start_index=0) 