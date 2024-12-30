from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os
import re
from datetime import datetime

def parse_transaction(text):
    """根据实际格式解析交易文本"""
    try:
        # 示例格式: "眼光不错赚的...(4Es) sold 1,018,901 ForexLens(aSC) ($0.00142 M:$1.42M) for 7.4289 SOL($1451.18) 1分钟前"
        data = {
            'account': '',
            'action': '',
            'amount': '',
            'token': '',
            'dollar_value': '',
            'sol_amount': '',
            'sol_value': '',
            'time': '',
            'raw_text': text
        }
        
        # 提取时间
        time_match = re.search(r'(\d+分钟前)', text)
        if time_match:
            data['time'] = time_match.group(1)
            
        # 提取账户名称
        account_match = re.search(r'^([^(]+)\(([^)]+)\)', text)
        if account_match:
            data['account'] = f"{account_match.group(1)}({account_match.group(2)})"
            
        # 提取操作类型 (bought/sold)
        if 'bought' in text:
            data['action'] = 'bought'
        elif 'sold' in text:
            data['action'] = 'sold'
            
        # 提取代币数量和名称
        token_match = re.search(r'(?:bought|sold)\s+([\d,]+)\s+([^(]+)\(([^)]+)\)', text)
        if token_match:
            data['amount'] = token_match.group(1).replace(',', '')
            data['token'] = f"{token_match.group(2)}({token_match.group(3)})"
            
        # 提取美元价值
        dollar_match = re.search(r'\((\$[^)]+)\)', text)
        if dollar_match:
            data['dollar_value'] = dollar_match.group(1)
            
        # 提取 SOL 数量和价值
        sol_match = re.search(r'(\d+\.?\d*)\s*SOL\(([^)]+)\)', text)
        if sol_match:
            data['sol_amount'] = sol_match.group(1)
            data['sol_value'] = f"${sol_match.group(2)}"
            
        return data
        
    except Exception as e:
        print(f"解析错误: {str(e)} - 文本: {text}")
        return {
            'account': '',
            'action': '',
            'amount': '',
            'token': '',
            'dollar_value': '',
            'sol_amount': '',
            'sol_value': '',
            'time': '',
            'raw_text': text
        }

def auto_login(driver):
    """自动登录功能"""
    try:
        time.sleep(5)
        print("尝试登录...")
        
        # 输入用户名
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        username_input.clear()
        username_input.send_keys('邮箱')
        print("已输入用户名")
        time.sleep(1)

        # 输入密码
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.clear()
        password_input.send_keys('密码')
        print("已输入密码")
        time.sleep(1)

        # 点击登录按钮
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '登录')]"))
        )
        login_button.click()
        print("已点击登录按钮")
        
        # 等待登录完成
        time.sleep(8)  # 增加等待时间
        return True
            
    except Exception as e:
        print(f"登录失败: {str(e)}")
        driver.save_screenshot("login_error.png")
        print("登录错误截图已保存为 login_error.png")
        return False

def scrape_data(driver):
    """抓取数据"""
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始抓取数据...")
        time.sleep(5)
        
        print("尝试获取交易记录...")
        
        # 使用更简单的JavaScript来获取所有文本内容
        js_script = """
        return Array.from(document.querySelectorAll('div'))
            .map(div => div.textContent)
            .filter(text => text && text.includes('SOL') && 
                          (text.includes('sold') || text.includes('bought')) && 
                          text.includes('分钟前') &&
                          text.length > 50);  // 确保是完整的交易记录
        """
        
        transaction_texts = driver.execute_script(js_script)
        
        if transaction_texts:
            print(f"找到 {len(transaction_texts)} 条潜在记录")
            # 打印前几条记录用于调试
            for i, text in enumerate(transaction_texts[:3]):
                print(f"示例记录 {i+1}: {text}")
            
            data = []
            seen_texts = set()
            
            for text in transaction_texts:
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    # 解析交易记录
                    try:
                        # 提取基本信息
                        account = re.search(r'^([^(]+)\(([^)]+)\)', text)
                        action = 'bought' if 'bought' in text else 'sold' if 'sold' in text else ''
                        amount = re.search(r'(?:bought|sold)\s+([\d,]+)', text)
                        token = re.search(r'(?:bought|sold)\s+[\d,]+\s+([^(]+)\(([^)]+)\)', text)
                        sol_info = re.search(r'([\d.]+)\s*SOL\(([^)]+)\)', text)
                        time_info = re.search(r'(\d+分钟前)', text)
                        
                        record = {
                            'account': account.group(0) if account else '',
                            'action': action,
                            'amount': amount.group(1).replace(',', '') if amount else '',
                            'token': f"{token.group(1)}({token.group(2)})" if token else '',
                            'sol_amount': sol_info.group(1) if sol_info else '',
                            'sol_value': sol_info.group(2) if sol_info else '',
                            'time': time_info.group(1) if time_info else '',
                            'raw_text': text
                        }
                        
                        if record['sol_amount']:  # 确保至少有SOL金额
                            data.append(record)
                            print(f"成功解析: {text[:100]}...")
                    except Exception as e:
                        print(f"解析记录失败: {str(e)}")
                        continue
            
            if data:
                # 将数据转换为DataFrame
                df = pd.DataFrame(data)
                
                # 保存到桌面
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                excel_path = os.path.join(desktop, f'chain_fm_data_{timestamp}.xlsx')
                df.to_excel(excel_path, index=False, encoding='utf-8')
                
                print(f'成功获取并保存 {len(data)} 条记录')
                print(f'数据已保存到: {excel_path}')
                return True
        
        print("未找到任何交易记录")
        # 保存页面源码以供调试
        with open('page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("已保存页面源码到 page_source.html")
        return False
        
    except Exception as e:
        print(f'获取数据时发生错误: {str(e)}')
        driver.save_screenshot("scrape_error.png")
        print("已保存错误截图到 scrape_error.png")
        return False

def main():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 访问登录页面
        driver.get('https://chain.fm/auth/sign-in')
        
        # 自动登录
        if not auto_login(driver):
            print("自动登录失败，程序退出")
            return
        
        print("登录成功，开始定时抓取数据...")
        
        # 等待页面完全加载
        time.sleep(10)
        
        # 循环抓取数据
        consecutive_failures = 0  # 连续失败次数
        while True:
            if scrape_data(driver):
                consecutive_failures = 0  # 重置失败计数
                print("等待1分钟后进行下一次抓取...")
                time.sleep(60)  # 等待1分钟
            else:
                consecutive_failures += 1
                if consecutive_failures >= 3:  # 连续失败3次
                    print("连续失败3次，尝试重新登录...")
                    driver.get('https://chain.fm/auth/sign-in')
                    time.sleep(3)
                    if not auto_login(driver):
                        print("重新登录失败，程序退出")
                        break
                    consecutive_failures = 0  # 重置失败计数
                else:
                    print(f"第 {consecutive_failures} 次抓取失败，等待10秒后重试...")
                    time.sleep(10)
    
    except KeyboardInterrupt:
        print("\n检测到键盘中断，程序正在退出...")
    except Exception as e:
        print(f'发生错误: {str(e)}')
    finally:
        driver.quit()

if __name__ == '__main__':
    main() 