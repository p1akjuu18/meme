import asyncio
import logging
import os
import pandas as pd
from datetime import datetime
import aiohttp
from typing import Dict, List, Optional
from data_analysis.token.support_resistance_analyzer import SupportResistanceAnalyzer
from real_time_running.real_time_update import TokenDataUpdater
import requests
import time
import traceback
import sys

# 设置控制台输出编码
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# 创建文件处理器
file_handler = logging.FileHandler('price_alert_debug.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class TelegramPriceAlert:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_ids = set()  # 使用set存储多个chat_id
        
        logger.info("正在初始化Telegram机器人...")
        
        # 获取程序所在目录并构建data文件夹路径
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_folder = os.path.join(self.current_dir, "data")
        self.token_info_file = os.path.join(self.data_folder, "merged_token_info_analyzed.xlsx")
        self.alert_history_file = os.path.join(self.data_folder, "alert_history.xlsx")
        
        # 确保文件夹存在
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            logger.info(f"创建文件夹: {self.data_folder}")
            
        self.support_analyzer = SupportResistanceAnalyzer(self.data_folder)
        self.price_alerts = {}
        self.token_info_data = self.load_token_info()
        
        # 加载保存的chat_ids
        self.load_chat_ids()
        
        # 如果没有chat_ids，尝试获取
        if not self.chat_ids:
            logger.info("没有找到已保存的chat_ids，尝试获取新的chat_ids...")
            self.get_chat_id()
            if self.chat_ids:
                logger.info(f"成功获取到 {len(self.chat_ids)} 个chat_id")
                self.save_chat_ids()
            else:
                logger.error("未能获取到任何chat_id")
        else:
            logger.info(f"已加载 {len(self.chat_ids)} 个已保存的chat_id")
            
        # 测试发送消息
        if self.chat_ids:
            test_message = "Telegram机器人初始化成功，开始监控价格..."
            if self.send_message(test_message):
                logger.info("测试消息发送成功")
            else:
                logger.error("测试消息发送失败")

    def load_token_info(self) -> pd.DataFrame:
        """加载代币详细信息"""
        try:
            # 查找以merged_token_info_analyzed开头的文件
            token_info_files = [f for f in os.listdir(self.data_folder) 
                              if f.startswith('merged_token_info_analyzed_') and f.endswith('.xlsx')]
            
            if not token_info_files:
                logger.warning(f"未找到merged_token_info_analyzed文件在: {self.data_folder}")
                return pd.DataFrame()
            
            # 获取最新的文件
            latest_file = sorted(token_info_files)[-1]
            file_path = os.path.join(self.data_folder, latest_file)
            
            logger.info(f"正在加载最新的代币信息文件: {latest_file}")
            df = pd.read_excel(file_path)
            logger.info(f"已加载代币信息文件，包含 {len(df)} 个代币")
            return df
        
        except Exception as e:
            logger.error(f"加载代币信息文件失败: {str(e)}")
            return pd.DataFrame()

    def get_token_info(self, token_symbol: str) -> Dict:
        """获取代币的详细信息"""
        if self.token_info_data.empty:
            return {}
            
        try:
            # 查找匹配的代币信息
            token_data = self.token_info_data[
                self.token_info_data['符号'].str.lower() == token_symbol.lower()
            ]
            
            if token_data.empty:
                logger.info(f"找不到代币 {token_symbol} 的信息，跳过")
                return {}
                
            return token_data.iloc[0].to_dict()
            
        except Exception as e:
            logger.error(f"获取代币 {token_symbol} 信息失败: {str(e)}")
            return {}

    def load_chat_ids(self):
        """从文件加载保存的chat_ids"""
        try:
            chat_ids_file = "telegram_chat_ids.txt"
            if os.path.exists(chat_ids_file):
                with open(chat_ids_file, "r") as f:
                    self.chat_ids = set(line.strip() for line in f if line.strip())
                logger.info(f"已加载 {len(self.chat_ids)} 个chat_id")
        except Exception as e:
            logger.error(f"加载chat_ids失败: {str(e)}")

    def save_chat_ids(self):
        """保存chat_ids到文件"""
        try:
            with open("telegram_chat_ids.txt", "w") as f:
                for chat_id in self.chat_ids:
                    f.write(f"{chat_id}\n")
        except Exception as e:
            logger.error(f"保存chat_ids失败: {str(e)}")

    def get_chat_id(self) -> None:
        """获取用户的chat_id"""
        try:
            # 调用 getUpdates API
            url = f"{self.base_url}/getUpdates"
            logger.info(f"正在获取chat_id，URL: {url}")
            
            response = requests.get(url)
            if not response.ok:
                logger.error(f"获取updates失败: {response.status_code} - {response.text}")
                return
                
            data = response.json()
            logger.info(f"获取到的updates数据: {data}")

            if not data.get('ok'):
                logger.error(f"API返回错误: {data.get('description', '未知错误')}")
                return

            # 检查是否有更新
            if not data.get('result'):
                logger.warning("没有找到任何更新，请确保已经和机器人进行过对话")
                return

            # 从更新中提取chat_id
            for update in data['result']:
                if 'message' in update and 'chat' in update['message']:
                    chat_id = str(update['message']['chat']['id'])
                    self.chat_ids.add(chat_id)
                    logger.info(f"找到新的chat_id: {chat_id}")

            if not self.chat_ids:
                logger.warning("未能从更新中找到任何chat_id")
            else:
                logger.info(f"成功获取到 {len(self.chat_ids)} 个chat_id")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求错误: {str(e)}")
        except Exception as e:
            logger.error(f"获取chat_id时出错: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")

    def send_message(self, message: str) -> bool:
        """发送消息到所有注册的chat_id"""
        if not self.chat_ids:
            logger.error("没有可用的chat_id，无法发送消息")
            return False
            
        success = True
        for chat_id in self.chat_ids:
            try:
                url = f"{self.base_url}/sendMessage"
                params = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                
                logger.info(f"正在向chat_id {chat_id} 发送消息...")
                response = requests.post(url, params=params)
                
                if response.ok:
                    response_data = response.json()
                    if response_data.get('ok'):
                        logger.info(f"消息成功发送到chat_id {chat_id}")
                    else:
                        logger.error(f"发送消息到chat_id {chat_id} 失败: {response_data.get('description', '未知错误')}")
                        success = False
                else:
                    logger.error(f"发送消息到chat_id {chat_id} 失败: {response.status_code} - {response.text}")
                    success = False
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"发送消息到chat_id {chat_id} 时网络错误: {str(e)}")
                success = False
            except Exception as e:
                logger.error(f"发送消息到chat_id {chat_id} 时出错: {str(e)}")
                logger.error(traceback.format_exc())
                success = False
                
        return success

    async def monitor_prices(self, check_interval: int = 900):
        """持续监控价格（与real_time_update同步，每15分钟更新一次）"""
        logger.info("开始价格监控...")
        logger.info("设置报警阈值: 1%")
        logger.info("更新间隔: 15分钟")
        
        while True:
            try:
                logger.info("开始新一轮价格检查...")
                token_count = 0
                alert_count = 0
                
                # 修改为查找new_alerts_开头的文件
                analysis_files = [f for f in os.listdir(self.support_analyzer.data_folder) 
                                if f.startswith('new_alerts_') and f.endswith('.csv')]
                
                if not analysis_files:
                    logger.warning("未找到支撑位分析文件")
                    await asyncio.sleep(check_interval)
                    continue
                    
                # 获取最新的分析文件
                latest_analysis = sorted(analysis_files)[-1]
                logger.info(f"使用最新的分析文件: {latest_analysis}")
                
                # 读取分析数据
                analysis_df = pd.read_csv(os.path.join(self.support_analyzer.data_folder, latest_analysis))
                
                # 处理每个代币的数据
                for token_symbol in analysis_df['token'].unique():
                    token_count += 1
                    token_data = analysis_df[analysis_df['token'] == token_symbol]
                    
                    if not token_data.empty:
                        current_price = token_data['current_price'].iloc[0]
                        support_levels = [
                            {
                                'price': row['support_level'],
                                'frequency': row['frequency']
                            }
                            for _, row in token_data.iterrows()
                        ]
                        
                        if support_levels:
                            logger.info(f"代币 {token_symbol} - 当前价格: {current_price}, 找到 {len(support_levels)} 个支撑位")
                            self.check_price_alerts(
                                token_symbol, 
                                current_price, 
                                support_levels,
                                threshold=0.01
                            )
                            alert_count += 1
                        else:
                            logger.info(f"代币 {token_symbol} 没有找到支撑位")
                            
                logger.info(f"本轮检查完成，共检查 {token_count} 个代币，处理 {alert_count} 个提醒")
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"监控过程中出错: {str(e)}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(60)  # 出错后等待1分钟再继续

    def save_alert_history(self, alert_data: Dict):
        """保存报警历史记录"""
        try:
            # 读取现有的报警历史记录
            if os.path.exists(self.alert_history_file):
                df = pd.read_excel(self.alert_history_file)
            else:
                df = pd.DataFrame()

            # 创建新的记录
            new_record = pd.DataFrame([alert_data])
            
            # 合并新旧记录
            df = pd.concat([df, new_record], ignore_index=True)
            
            # 保存到Excel文件
            df.to_excel(self.alert_history_file, index=False)
            logger.info(f"报警记录已保存到: {self.alert_history_file}")
            
        except Exception as e:
            logger.error(f"保存报警记录失败: {str(e)}")

    def check_price_alerts(self, token_symbol: str, current_price: float, 
                          support_levels: List[Dict], threshold: float = 0.01) -> None:
        """检查价格是否接近支撑位并发送提醒"""
        # 获取代币的详细信息
        token_info = self.get_token_info(token_symbol)
        
        # 检查关键数据是否存在
        if not token_info or not token_info.get('代币地址') or not token_info.get('名称'):
            logger.warning(f"代币 {token_symbol} 缺少关键信息: 地址={token_info.get('代币地址') if token_info else 'None'}, 名称={token_info.get('名称') if token_info else 'None'}")
            return
            
        for level in support_levels:
            # 只处理频次大于3的支撑位
            if level['frequency'] <= 3:
                logger.debug(f"代币 {token_symbol} 支撑位 {level['price']} 的频次 {level['frequency']} <= 3，跳过")
                continue
            
            price_diff = abs(current_price - level['price']) / level['price']
            logger.debug(f"代币 {token_symbol} - 当前价格: {current_price}, 支撑位: {level['price']}, 差距: {price_diff*100:.2f}%")
            
            # 生成警报的唯一标识
            alert_id = f"{token_symbol}_{level['price']:.8f}"
            
            # 如果价格接近支撑位（1%以内）
            if price_diff < threshold:
                current_time = time.time()
                
                # 检查是否在4小时内已经发送过警报
                if alert_id in self.price_alerts:
                    last_alert_time = self.price_alerts[alert_id]
                    time_diff = current_time - last_alert_time
                    
                    # 如果在4小时内已经发送过警报，跳过
                    if time_diff < 14400:  # 4小时 = 14400秒
                        logger.info(f"代币 {token_symbol} 在4小时内已经发送过警报，距离上次警报: {time_diff/3600:.2f}小时")
                        continue
                
                logger.info(f"代币 {token_symbol} 触发价格警报 - 当前价格: {current_price}, 支撑位: {level['price']}, 差距: {price_diff*100:.2f}%")
                
                # 获取代币基本信息
                token_name = token_info.get('名称', '')
                token_symbol = token_info.get('符号', '')
                token_address = token_info.get('代币地址', '')
                fully_diluted_mcap = token_info.get('完全稀释估值(USD)', 0)  # 获取完全稀释市值
                price_in_info = token_info.get('价格(USD)', 0)  # 获取价格列的价格
                daytime = token_info.get('代币存活天数', 0)  # 获取代币存活列的价格

                # 计算当前市值
                market_cap_usd = (fully_diluted_mcap / price_in_info) * current_price if price_in_info != 0 else 0
                
                # 处理市值显示单位
                def format_market_cap(value):
                    if value >= 1_000_000_000:  # 十亿以上用B
                        return f"{value/1_000_000_000:.2f}B"
                    elif value >= 1_000_000:  # 百万以上用M
                        return f"{value/1_000_000:.2f}M"
                    elif value >= 1_000:  # 千以上用K
                        return f"{value/1_000:.2f}K"
                    else:
                        return f"{value:.2f}"
                
                # 构建基本信息部分
                message = (
                    f"📊Support Signal\n"
                    f"<a href='https://gmgn.ai/sol/token/{token_address}?ref=oPV6XLFT'>{token_symbol} - {token_name}</a>\n"
                    f"<code>{token_address}</code>\n\n"
                    f"🔍代币信息\n"
                    f"市值: {format_market_cap(market_cap_usd)}\n"
                )

                # 添加社交媒体信息
                twitter = token_info.get('twitter_handle', '')
                telegram = token_info.get('telegram_handle', '')
                websites = token_info.get('websites', '')
                
                social_links = []
                if twitter and not pd.isna(twitter): 
                    social_links.append(f"<a href='https://twitter.com/{twitter}'>推特 ✓</a>")
                else: 
                    social_links.append("推特 X")
                if telegram and not pd.isna(telegram): 
                    social_links.append(f"<a href='https://t.me/{telegram}'>电报 ✓</a>")
                else: 
                    social_links.append("电报 X")
                if websites and not pd.isna(websites): 
                    social_links.append(f"<a href='{websites}'>官网 ✓</a>")
                else: 
                    social_links.append("官网 X")
                
                message += " | ".join(social_links) + "\n"
                # 构建X搜索链接
                x_search_links = []
                
                # 添加名称搜索链接（普通搜索）
                if token_name:
                    name_search = f"<a href='https://x.com/search?q={token_name}&src=typed_query'>名称</a>"
                    x_search_links.append(name_search)
                else:
                    x_search_links.append("名称")
                
                # 添加地址搜索链接（普通搜索）
                if token_address:
                    address_search = f"<a href='https://x.com/search?q={token_address}&src=typed_query&f=top'>地址</a>"
                    x_search_links.append(address_search)
                else:
                    x_search_links.append("地址")
                
                # 添加中文官网搜索（指定中文搜索）
                if token_name:
                    website_search = f"<a href='https://x.com/search?q={token_name}%20lang:zh-cn&src=typed_query'>中文搜索</a>"
                    x_search_links.append(website_search)
                else:
                    x_search_links.append("中文")
                
                message += f"X搜索: {' | '.join(x_search_links)}\n\n"
            
                
                # 添加聪明钱信息
                wallet_count = token_info.get('买入钱包数', 0)
                wallet_balance = token_info.get('聪明钱包总余额', 0)
                
                # 处理NaN值
                if pd.isna(wallet_count):
                    wallet_count = 0
                if pd.isna(wallet_balance):
                    wallet_balance = 0
                
                # 处理余额单位
                wallet_balance = float(wallet_balance)
                if wallet_balance >= 1000000:
                    wallet_balance_str = f"{wallet_balance/1000000:.2f}M"
                elif wallet_balance >= 1000:
                    wallet_balance_str = f"{wallet_balance/1000:.2f}K"
                else:
                    wallet_balance_str = f"{wallet_balance:.2f}"
                    
                message += (
                    f"🔔聪明钱数据\n"
                    f"持有钱包数: {int(wallet_count)}\n"
                    f"聪明钱包总余额: {wallet_balance_str}\n\n"
                )

                # 添加价格历史信息
                ath = token_info.get('ATH', 0)
                max_drawdown = token_info.get('max_drawdown_percentage', 0)
                create_time = token_info.get('创建时间', '未知')
                daytime = token_info.get('代币存活天数', 0)
                
                # 处理NaN值
                if pd.isna(ath):
                    ath = 0
                if pd.isna(max_drawdown):
                    max_drawdown = 0
                if pd.isna(create_time):
                    create_time = "未知"
                else:
                    create_time = str(create_time).replace('T', ' ').replace('Z', '')
                if pd.isna(daytime):
                    daytime = 0
                
                ath = float(ath) / 1000000  # 转换为M单位
                
                message += (
                    f"📊价格历史\n"
                    f"ATH: {ath:.2f}M\n"
                    f"最大回撤: {float(max_drawdown):.2f}%\n"
                    f"存活天数: {int(daytime)}天\n\n"
                )
                
                # 添加代币描述
                description = token_info.get('description', '该代币没有描述信息')
                if description and isinstance(description, str):
                    if len(description) > 200:  # 如果描述太长，截断它
                        description = description[:197] + "..."
                else:
                    description = '该代币没有描述信息'
                message += (
                    f"📝代币简介\n"
                    f"{description}\n\n"
                )
                
                # 添加价格预警信息
                message += (
                    f"⚠️价格预警\n"
                    f"当前价格: {current_price:.5f}\n"
                    f"支撑位: {level['price']:.5f}\n"
                    f"支撑位频次: {level['frequency']}\n"
                    f"距离: {price_diff*100:.2f}%\n\n"
                )

              
                if self.send_message(message):
                    # 记录已发送的警报时间
                    self.price_alerts[alert_id] = current_time
                    
                    # 保存报警记录
                    alert_record = {
                        '报警时间': datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S'),
                        '代币地址': token_address,
                        '代币名称': token_name,
                        '代币简称': token_symbol,
                        '当前价格': current_price,
                        '当前市值': market_cap_usd,
                        '支撑位': level['price'],
                        '支撑位频次': level['frequency'],
                        '距离支撑位': f"{price_diff*100:.2f}%",
                        '持有钱包数': int(wallet_count),
                        '聪明钱包总余额': wallet_balance,
                        'ATH': token_info.get('ATH', 0),
                        '最大回撤': token_info.get('max_drawdown_percentage', 0),
                        '创建时间': token_info.get('创建时间', '未知'),
                        '代币存活天数': int(daytime),
                        'Twitter': token_info.get('twitter_handle', ''),
                        'Telegram': token_info.get('telegram_handle', ''),
                        '官网': token_info.get('websites', '')
                    }
                    self.save_alert_history(alert_record)
                else:
                    logger.error(f"❌ 警报发送失败: {token_symbol}")
            
            # 如果价格远离支撑位，清除之前的警报记录
            elif price_diff >= threshold and alert_id in self.price_alerts:
                del self.price_alerts[alert_id]

async def main():
    # Telegram机器人配置
    TOKEN = "7987851125:AAEei6dBYjOZoQt5Ib4d4Wx97laBvSy6Oh4"
    
    # 创建价格提醒实例
    alert_system = TelegramPriceAlert(TOKEN)
    
    # 开始监控价格
    await alert_system.monitor_prices()

if __name__ == "__main__":
    asyncio.run(main()) 