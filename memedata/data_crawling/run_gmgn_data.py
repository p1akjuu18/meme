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

def process_address(address, retry_count=5):
    """处理单个地址的数据采集"""
    url = f"https://gmgn.ai/sol/address/{address}"
    
    for attempt in range(retry_count):
        driver = None
        try:
            print(f"\n尝试第 {attempt + 1} 次处理地址: {address}")
            driver = create_new_driver()
            driver.set_page_load_timeout(120)  # 增加页面加载超时时间到120秒
            driver.get(url)
            
            # 增加初始等待时间
            time.sleep(10)
            
            # 获取表格数据
            table_data = None
            try:
                # 增加等待时间到60秒
                table = WebDriverWait(driver, 60).until(
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

            # 获取所有链接
            link_data = []
            for selector in [
                "#tabs-leftTabs--tabpanel-1 table tbody tr td.g-table-cell a",
                "table tbody tr td.g-table-cell.g-table-cell-fix-left a",
                "a.css-1qtqy4u"
            ]:
                links = driver.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        link_data.append({
                            'Link URL': href,
                            'Link Text': text,
                            'Source Address': address,
                            'Source URL': url
                        })
                    except Exception as e:
                        print(f"处理链接时出错: {str(e)}")
                        continue
            
            link_data = pd.DataFrame(link_data) if link_data else None

            # 获取JSON数据
            json_data = None
            try:
                script_tag = WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, '//script[@id="__NEXT_DATA__"]'))
                )
                if script_tag:
                    json_data = json.loads(script_tag.get_attribute('innerHTML'))
            except Exception as e:
                print(f"获取JSON数据时出错: {str(e)}")

            return True, json_data, table_data, link_data

        except Exception as e:
            print(f"处理地址 {address} 时出错: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(random.uniform(10, 15))
            else:
                return False, None, None, None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

def run_gmgn_data(addresses):
    print(f"开始运行数据采集程序 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 设置输出文件路径
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    date_str = datetime.now().strftime('%Y%m%d_%H%M')
    
    # 创建输出文件
    json_output_file = os.path.join(desktop_path, f"raw_json_data_{date_str}.json")
    table_output_file = os.path.join(desktop_path, f"raw_table_data_{date_str}.xlsx")
    links_output_file = os.path.join(desktop_path, f"raw_links_data_{date_str}.xlsx")
    
    all_json_data = {}
    all_table_data = []
    all_links_data = []
    
    print(f"将处理所有地址，总计: {len(addresses)} 个地址")
    
    # 统计变量
    successful_requests = 0
    total_table_rows = 0
    total_link_rows = 0
    
    for idx, address in enumerate(addresses):
        print(f"\n处理进度: {idx+1}/{len(addresses)}")
        
        success, json_data, table_data, links_data = process_address(address)
        
        if success:
            successful_requests += 1
            
            # 统计数据
            if json_data:
                all_json_data[address] = json_data
            
            if table_data is not None and not table_data.empty:
                all_table_data.append(table_data)
                total_table_rows += len(table_data)
            
            if links_data is not None and not links_data.empty:
                all_links_data.append(links_data)
                total_link_rows += len(links_data)
            
            # 每10个地址显示一次统计信息
            if (idx + 1) % 10 == 0:
                print(f"\n========= 第{idx+1}个地址统计 =========")
                print(f"已成功请求数: {successful_requests}/{idx+1}")
                print(f"累计表格数据: {total_table_rows}行")
                print(f"累计链接数据: {total_link_rows}行")
                print(f"当前数据比例(链接/表格): {total_link_rows/total_table_rows if total_table_rows > 0 else 0:.2f}")
                print("================================\n")
                
                # 保存数据
                with open(json_output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_json_data, f, indent=4, ensure_ascii=False)
                
                if all_table_data:
                    pd.concat(all_table_data, ignore_index=True).to_excel(table_output_file, index=False)
                
                if all_links_data:
                    pd.concat(all_links_data, ignore_index=True).to_excel(links_output_file, index=False)
        
        # 等待时间
        wait_time = random.uniform(3, 8)
        time.sleep(wait_time)
        
        # 每20个地址的额外等待
        if (idx + 1) % 20 == 0:
            long_wait = random.uniform(15, 30)
            print(f"\n已处理20个地址，暂停 {long_wait:.2f} 秒...")
            time.sleep(long_wait)
    
    # 最终保存
    with open(json_output_file, 'w', encoding='utf-8') as f:
        json.dump(all_json_data, f, indent=4, ensure_ascii=False)
    
    if all_table_data:
        final_table_data = pd.concat(all_table_data, ignore_index=True)
        final_table_data.to_excel(table_output_file, index=False)
    
    if all_links_data:
        final_links_data = pd.concat(all_links_data, ignore_index=True)
        final_links_data.to_excel(links_output_file, index=False)
    
    print("\n数据采集完成！")

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