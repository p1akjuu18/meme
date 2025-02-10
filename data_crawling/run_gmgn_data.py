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
    """从Excel或CSV文件读取地址列表"""
    try:
        # 设置默认编码
        if sys.stdout.encoding != 'utf-8':
            print(f"当前系统编码: {sys.stdout.encoding}")
            try:
                import codecs
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
                print("已将标准输出编码设置为 UTF-8")
            except Exception as e:
                print(f"设置编码失败: {str(e)}")

        # 获取当前工作目录
        current_dir = os.getcwd()
        print(f"当前工作目录: {current_dir}")
        
        # 尝试读取CSV文件
        filename_csv = "merge_owner_20241229.csv"
        csv_path = os.path.join(current_dir, filename_csv)
        
        if os.path.exists(csv_path):
            print(f"找到CSV文件: {csv_path}")
            try:
                # 先尝试检测文件编码
                import chardet
                with open(csv_path, 'rb') as file:
                    raw_data = file.read()
                    result = chardet.detect(raw_data)
                    detected_encoding = result['encoding']
                    print(f"检测到的文件编码: {detected_encoding}")
                
                # 使用检测到的编码读取文件
                df = pd.read_csv(csv_path, encoding=detected_encoding)
                print("成功读取CSV文件")
            except Exception as e:
                print(f"使用检测到的编码读取失败: {str(e)}")
                print("尝试使用其他编码方式...")
                
                # 尝试不同的编码方式
                encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
                for encoding in encodings:
                    try:
                        print(f"尝试使用 {encoding} 编码读取...")
                        df = pd.read_csv(csv_path, encoding=encoding)
                        print(f"使用 {encoding} 编码成功读取文件")
                        break
                    except Exception as e:
                        print(f"使用 {encoding} 编码失败: {str(e)}")
                else:
                    raise Exception("所有编码方式都失败了")
        else:
            print(f"未找到CSV文件，尝试读取Excel文件")
            # 尝试读取Excel文件
            filename_xlsx = "merge_owner_20241229.xlsx"
            excel_path = os.path.join(current_dir, filename_xlsx)
            
            if not os.path.exists(excel_path):
                print(f"错误：未找到输入文件")
                return None
                
            print(f"找到Excel文件: {excel_path}")
            try:
                # 读取Excel文件
                df = pd.read_excel(excel_path)
                print("成功读取Excel文件")
            except Exception as e:
                print(f"读取Excel文件失败: {str(e)}")
                try:
                    print("尝试使用openpyxl引擎...")
                    df = pd.read_excel(excel_path, engine='openpyxl')
                    print("使用openpyxl引擎成功读取文件")
                except Exception as e:
                    print(f"使用openpyxl引擎失败: {str(e)}")
                    return None
        
        if 'address' not in df.columns:
            print("错误：文件中未找到'address'列")
            print(f"可用的列名: {df.columns.tolist()}")
            return None
            
        # 获取地址列表并去除可能的空值和重复值
        addresses = df['address'].dropna().unique().tolist()
        print(f"成功读取到 {len(addresses)} 个唯一地址")
        return addresses
        
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        print(f"错误类型: {type(e)}")
        print(f"错误详情: {traceback.format_exc()}")
        return None

def create_new_driver():
    """创建新的driver实例"""
    try:
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 添加一些新的选项来提高稳定性
        options.add_argument('--disable-web-security')  # 禁用网页安全性检查
        options.add_argument('--disable-blink-features=AutomationControlled')  # 避免被检测为自动化工具
        options.add_argument('--disable-infobars')  # 禁用信息栏
        options.add_argument('--disable-popup-blocking')  # 禁用弹窗阻止
        options.add_argument('--disable-notifications')  # 禁用通知
        
        # 保留原有的安全选项
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-extensions')
        
        # 禁用日志输出
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_settings.popups": 0
        })

        try:
            service = Service(ChromeDriverManager().install())
            service.log_path = os.devnull
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            print(f"创建driver失败: {str(e)}")
            time.sleep(5)
            try:
                # 使用 taskkill /f /im 命令可能不够，添加更多进程清理命令
                os.system('taskkill /f /im chrome.exe >nul 2>&1')
                os.system('taskkill /f /im chromedriver.exe >nul 2>&1')
                os.system('wmic process where name="chrome.exe" delete >nul 2>&1')
                os.system('wmic process where name="chromedriver.exe" delete >nul 2>&1')
                time.sleep(2)
                
                service = Service(ChromeDriverManager().install())
                service.log_path = os.devnull
                driver = webdriver.Chrome(service=service, options=options)
                return driver
            except Exception as e:
                print(f"重试创建driver仍然失败: {str(e)}")
                raise e

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
            driver.set_page_load_timeout(120)
            driver.get(url)
            
            # 增加初始等待时间
            time.sleep(15)
            
            # 滚动页面以加载更多数据
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 10  # 最多滚动10次
            
            while scroll_count < max_scrolls:
                # 滚动到页面底部
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # 等待新内容加载
                
                # 计算新的滚动高度
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # 如果高度没有变化，说明已经到底部
                    break
                    
                last_height = new_height
                scroll_count += 1
            
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
                print(f"成功获取到 {len(data)} 条持仓数据")
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
    data_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    date_str = datetime.now().strftime('%Y%m%d_%H%M')
    
    # 创建输出文件
    json_output_file = os.path.join(data_dir, f"raw_json_data_{date_str}.json")
    table_output_file = os.path.join(data_dir, f"raw_table_data_{date_str}.xlsx")
    links_output_file = os.path.join(data_dir, f"raw_links_data_{date_str}.xlsx")
    
    # 分批处理的大小
    batch_size = 50
    current_batch = []
    current_links_batch = []
    
    print(f"将处理所有地址，总计: {len(addresses)} 个地址")
    
    # 统计变量
    successful_requests = 0
    total_table_rows = 0
    total_link_rows = 0
    
    def save_batch_data(batch_data, output_file, batch_num, data_type="table"):
        """保存一批数据"""
        if not batch_data:
            return
            
        try:
            combined_data = pd.concat(batch_data, ignore_index=True)
            # 如果文件不存在，直接保存
            if not os.path.exists(output_file):
                combined_data.to_excel(output_file, index=False, engine='openpyxl')
                print(f"第 {batch_num} 批{data_type}数据已保存到新文件: {output_file}")
            else:
                # 如果文件存在，读取现有数据并追加
                try:
                    existing_data = pd.read_excel(output_file, engine='openpyxl')
                    updated_data = pd.concat([existing_data, combined_data], ignore_index=True)
                    updated_data.to_excel(output_file, index=False, engine='openpyxl')
                    print(f"第 {batch_num} 批{data_type}数据已追加到现有文件")
                except Exception as e:
                    # 如果读取现有文件失败，尝试直接保存为新文件
                    backup_file = output_file.replace('.xlsx', f'_batch_{batch_num}.xlsx')
                    combined_data.to_excel(backup_file, index=False, engine='openpyxl')
                    print(f"无法追加到现有文件，已保存为新文件: {backup_file}")
        except Exception as e:
            print(f"保存第 {batch_num} 批{data_type}数据时出错: {str(e)}")
            # 尝试保存为CSV
            try:
                csv_file = output_file.replace('.xlsx', f'_batch_{batch_num}.csv')
                combined_data.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"已将第 {batch_num} 批{data_type}数据保存为CSV格式: {csv_file}")
            except Exception as e:
                print(f"保存CSV也失败了: {str(e)}")
    
    all_json_data = {}
    batch_num = 1
    
    for idx, address in enumerate(addresses):
        print(f"\n处理进度: {idx+1}/{len(addresses)}")
        
        success, json_data, table_data, links_data = process_address(address)
        
        if success:
            successful_requests += 1
            
            # 处理JSON数据
            if json_data:
                all_json_data[address] = json_data
                # 定期保存JSON数据
                if len(all_json_data) % batch_size == 0:
                    with open(json_output_file, 'w', encoding='utf-8') as f:
                        json.dump(all_json_data, f, indent=4, ensure_ascii=False)
            
            # 处理表格数据
            if table_data is not None and not table_data.empty:
                current_batch.append(table_data)
                total_table_rows += len(table_data)
            
            # 处理链接数据
            if links_data is not None and not links_data.empty:
                current_links_batch.append(links_data)
                total_link_rows += len(links_data)
            
            # 当达到批处理大小时保存数据
            if len(current_batch) >= batch_size:
                print(f"\n保存第 {batch_num} 批数据...")
                save_batch_data(current_batch, table_output_file, batch_num, "表格")
                save_batch_data(current_links_batch, links_output_file, batch_num, "链接")
                current_batch = []
                current_links_batch = []
                batch_num += 1
            
            # 显示统计信息
            if (idx + 1) % 10 == 0:
                print(f"\n========= 第{idx+1}个地址统计 =========")
                print(f"已成功请求数: {successful_requests}/{idx+1}")
                print(f"累计表格数据: {total_table_rows}行")
                print(f"累计链接数据: {total_link_rows}行")
                print(f"当前数据比例(链接/表格): {total_link_rows/total_table_rows if total_table_rows > 0 else 0:.2f}")
                print("================================\n")
        
        # 等待时间
        wait_time = random.uniform(3, 8)
        time.sleep(wait_time)
        
        # 每20个地址的额外等待
        if (idx + 1) % 20 == 0:
            long_wait = random.uniform(15, 30)
            print(f"\n已处理20个地址，暂停 {long_wait:.2f} 秒...")
            time.sleep(long_wait)
    
    # 保存最后一批数据
    if current_batch:
        print("\n保存最后一批数据...")
        save_batch_data(current_batch, table_output_file, batch_num, "表格")
        save_batch_data(current_links_batch, links_output_file, batch_num, "链接")
    
    # 保存最终的JSON数据
    with open(json_output_file, 'w', encoding='utf-8') as f:
        json.dump(all_json_data, f, indent=4, ensure_ascii=False)
    
    print("\n数据采集完成！")

def main():
    # 读取地址列表
    addresses = read_addresses()
    if not addresses:
        print("无法继续执行：未能成功读取地址列表")
        return
    
    print(f"\n准备处理 {len(addresses)} 个地址")
    # 直接运行数据采集程序
    run_gmgn_data(addresses)

if __name__ == "__main__":
    main() 