import subprocess
import sys
import os
import pandas as pd
from datetime import datetime
import time
import random
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

def read_addresses():
    """从Excel文件读取地址列表"""
    try:
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        excel_path = os.path.join(desktop_path, "merged_owner_20241229.xlsx")
        
        if not os.path.exists(excel_path):
            print(f"错误：未找到文件 {excel_path}")
            return None
            
        # 读取Excel文件
        df = pd.read_excel(excel_path)
        
        if 'address' not in df.columns:
            print("错误：Excel文件中未找到'address'列")
            return None
            
        # 获取地址列表并去除可能的空值和重复值
        addresses = df['address'].dropna().unique().tolist()
        addresses = addresses[275:]  # 只处理第275行之后的数据
        print(f"成功读取到 {len(addresses)} 个唯一地址")
        return addresses
        
    except Exception as e:
        print(f"读取Excel文件时出错: {str(e)}")
        return None

def create_new_driver():
    """创建新的driver实例"""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 保留基本的安全选项
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-extensions')
    
    options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 移除JavaScript禁用设置
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.images": 2
    })

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"创建driver失败: {str(e)}")
        raise e

def process_address(address, retry_count=3):
    """处理单个地址的数据采集"""
    url = f"https://gmgn.ai/sol/address/{address}"
    
    for attempt in range(retry_count):
        driver = None
        try:
            print(f"\n尝试第 {attempt + 1} 次处理地址: {address}")
            driver = create_new_driver()
            driver.set_page_load_timeout(60)  # 增加超时时间
            
            # 访问页面
            driver.get(url)
            print(f"正在加载页面: {url}")
            
            # 增加页面加载等待时间
            time.sleep(5)  # 添加固定等待时间
            
            # 等待页面加载完成
            WebDriverWait(driver, 90).until(  # 增加等待时间
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # 检查页面是否加载成功
            if "Error" in driver.title or "404" in driver.title:
                print(f"页面加载失败: {driver.title}")
                raise Exception("页面加载失败")
            
            # 等待表格容器加载
            try:
                WebDriverWait(driver, 90).until(  # 增加等待时间
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#tabs-leftTabs--tabpanel-1'))
                )
            except:
                print("等待表格容器超时，尝试直接获取表格")
            
            # 获取表格数据
            try:
                table = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, '//table'))
                )
                table_html = table.get_attribute('outerHTML')
                soup = BeautifulSoup(table_html, 'html.parser')
                headers = [header.text.strip() for header in soup.find_all('th')]
                
                rows = soup.find_all('tr')
                data = []
                for row in rows:
                    cols = row.find_all('td')
                    if cols:
                        row_data = [col.text.strip() for col in cols]
                        data.append(row_data)
                
                table_data = pd.DataFrame(data, columns=headers)
                table_data["Source URL"] = url
            except Exception as e:
                print(f"获取表格数据时出错: {str(e)}")
                table_data = None
            
            # 2. 处理链接数据
            selectors = [
                "#tabs-leftTabs--tabpanel-1 table tbody tr td.g-table-cell a",
                "table tbody tr td.g-table-cell.g-table-cell-fix-left a",
                "a.css-1qtqy4u"
            ]
            
            for selector in selectors:
                print(f"尝试选择器: {selector}")
                links = driver.find_elements(By.CSS_SELECTOR, selector)
                if links:
                    token_data = []
                    
                    for i in range(0, len(links), 3):
                        try:
                            if i + 2 >= len(links):
                                break
                                
                            # 获取地址
                            addr_href = links[i].get_attribute('href')
                            if 'sol/token/' in addr_href:
                                token_address = addr_href.split('token/')[-1]
                                
                                # 获取名称
                                name_link = links[i + 2]
                                token_name = name_link.text.strip()
                                if token_name.startswith('$'):
                                    token_name = token_name[1:]
                                elif not token_name:
                                    name_href = name_link.get_attribute('href')
                                    if 'search?q=$' in name_href:
                                        token_name = name_href.split('search?q=$')[-1]
                                
                                token_data.append({
                                    'Token Address': token_address,
                                    'Token Name': token_name,
                                    'Source URL': url
                                })
                                    
                        except Exception as e:
                            print(f"处理链接组时出错: {str(e)}")
                            continue
                    
                    if token_data:
                        link_data = pd.DataFrame(token_data)
                    break
            
            # 获取 JSON 数据
            script_tag = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//script[@id="__NEXT_DATA__"]'))
            )
            
            json_data = None
            if script_tag:
                json_data = json.loads(script_tag.get_attribute('innerHTML'))
            
            return True, json_data, table_data, link_data
                
        except Exception as e:
            print(f"处理地址 {address} 时出错: {str(e)}")
            if attempt < retry_count - 1:
                delay = random.uniform(10, 15)
                print(f"等待 {delay:.2f} 秒后重试...")
                time.sleep(delay)
            else:
                print(f"已达到最大重试次数，跳过地址: {address}")
                return False, None, None, None
                
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            if attempt < retry_count - 1:
                time.sleep(random.uniform(5, 8))

def run_gmgn_data(addresses):
    print(f"开始运行数据采集程序 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 设置输出文件路径
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    date_str = datetime.now().strftime('%Y%m%d_%H%M')
    json_output_file = os.path.join(desktop_path, f"json_data_{date_str}.json")
    html_output_file = os.path.join(desktop_path, f"html_table_data_{date_str}.xlsx")
    
    # 如果JSON文件存在，读取现有数据
    all_json_data = {}
    if os.path.exists(json_output_file):
        try:
            with open(json_output_file, 'r', encoding='utf-8') as f:
                all_json_data = json.load(f)
        except Exception as e:
            print(f"读取现有JSON数据时出错: {str(e)}")
    
    # 如果Excel文件存在，读取现有数据
    all_html_data = pd.DataFrame()
    if os.path.exists(html_output_file):
        try:
            all_html_data = pd.read_excel(html_output_file)
        except Exception as e:
            print(f"读取现有Excel数据时出错: {str(e)}")
    
    processed_count = 0
    
    for address in addresses:
        processed_count += 1
        print(f"\n处理进度: {processed_count}/{len(addresses)}")
        print(f"正在处理地址: {address}")
        
        success, json_data, table_data, link_data = process_address(address)
        
        if success:
            # 保存JSON数据
            if json_data:
                all_json_data[address] = json_data
                try:
                    with open(json_output_file, 'w', encoding='utf-8') as f:
                        json.dump(all_json_data, f, indent=4, ensure_ascii=False)
                    print(f"JSON数据已更新保存: {json_output_file}")
                except Exception as e:
                    print(f"保存JSON数据时出错: {str(e)}")
            
            # 保存表格数据和链接数据
            try:
                if table_data is not None and not table_data.empty:
                    if link_data is not None and not link_data.empty:
                        # 重命名link_data中的Source URL列，避免重复
                        link_data = link_data.rename(columns={'Source URL': 'Token Source URL'})
                        
                        # 确保两个DataFrame都有数据再合并
                        min_rows = min(len(table_data), len(link_data))
                        table_data = table_data.iloc[:min_rows].copy()
                        link_data = link_data.iloc[:min_rows].copy()
                        
                        # 合并数据
                        current_data = pd.concat([table_data, link_data], axis=1)
                        
                        # 删除可能的重复列或无用列
                        columns_to_drop = [col for col in current_data.columns if 'Unnamed:' in col]
                        if columns_to_drop:
                            current_data = current_data.drop(columns=columns_to_drop)
                    else:
                        current_data = table_data.copy()
                    
                    # 确保all_html_data已初始化
                    if all_html_data is None or all_html_data.empty:
                        all_html_data = current_data
                    else:
                        # 使用当前数据的列
                        all_html_data = pd.concat([all_html_data, current_data], ignore_index=True)
                    
                    # 保存到Excel前先检查文件是否被占用
                    try:
                        if os.path.exists(html_output_file):
                            try:
                                with open(html_output_file, 'a+b') as f:
                                    pass
                            except PermissionError:
                                base, ext = os.path.splitext(html_output_file)
                                html_output_file = f"{base}_{random.randint(1,1000)}{ext}"
                                print(f"原文件被占用，将保存到新文件: {html_output_file}")
                        
                        all_html_data.to_excel(html_output_file, index=False)
                        print(f"数据已更新保存到: {html_output_file}")
                    except Exception as e:
                        print(f"保存到Excel文件失败: {str(e)}")
                        try:
                            backup_file = os.path.join(desktop_path, f"backup_data_{date_str}.xlsx")
                            all_html_data.to_excel(backup_file, index=False)
                            print(f"数据已保存到备用文件: {backup_file}")
                        except Exception as e2:
                            print(f"保存到备用文件也失败: {str(e2)}")
                else:
                    print("没有有效的表格数据可保存")
            except Exception as e:
                print(f"处理数据时出错: {str(e)}")
                traceback.print_exc()
            
            print(f"成功处理并保存地址: {address}")
        else:
            print(f"处理地址失败: {address}")
        
        if processed_count < len(addresses):
            delay = random.uniform(0, 5)
            print(f"等待 {delay:.2f} 秒后处理下一个地址...")
            time.sleep(delay)
    
    print("=" * 50)
    print(f"数据采集完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return True

def main():
    # 读取地址列表
    addresses = read_addresses()
    if not addresses:
        print("无法继续执行：未能成功读取地址列表")
        return
    
    # 确认是否继续
    print(f"\n准备处理 {len(addresses)} 个地址")
    confirm = input("是否继续？(y/n): ")
    if confirm.lower() != 'y':
        print("程序已取消")
        return
        
    # 运行数据采集程序
    run_gmgn_data(addresses)

if __name__ == "__main__":
    main() 