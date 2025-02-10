# 加密货币监控系统

## 项目说明
这是一个加密货币价格监控和服务器管理系统，包含以下功能：
- 实时价格监控
- 支撑位分析
- Telegram价格提醒
- 服务器性能监控
- 数据采集和清洗

## 数据采集模块
### GMGN数据采集 (run_gmgn_data.py)
- 从GMGN.ai采集代币交易数据
- 支持批量地址处理
- 自动处理反爬虫机制
- 保存为JSON和Excel格式

### 历史数据获取 (get_historical_data.py)
- 使用CoinGecko API获取历史价格数据
- 支持15分钟K线数据
- 需要CoinGecko API密钥
- 自动保存为CSV格式

### Chain.fm数据采集 (chain_fm_scraper.py)
- 实时监控Chain.fm交易数据
- 自动登录和会话管理
- 交易数据解析和格式化
- 需要Chain.fm账号凭据

### 数据清洗工具 (volume_data_cleaner.py)
- 交易量过滤
- 交易次数验证
- 市值筛选
- 自动输出清洗后的数据

## 安装步骤

1. 安装Python环境（需要Python 3.8或更高版本）

2. 安装Chrome浏览器和ChromeDriver：
   - 下载并安装 [Google Chrome](https://www.google.com/chrome/)
   - ChromeDriver会通过webdriver_manager自动安装

3. 安装依赖包：
```bash
pip install -r requirements.txt
```

4. 设置环境变量：
```bash
# Windows
set COINGECKO_API_KEY=你的API密钥
set TELEGRAM_TOKEN=你的Telegram机器人Token

# Linux/Mac
export COINGECKO_API_KEY=你的API密钥
export TELEGRAM_TOKEN=你的Telegram机器人Token
```

5. 配置Chain.fm凭据：
   - 在chain_fm_scraper.py中设置登录信息：
   ```python
   username_input.send_keys('你的Chain.fm邮箱')
   password_input.send_keys('你的Chain.fm密码')
   ```

6. 创建必要的目录：
```bash
# Windows
mkdir "%USERPROFILE%\Desktop\token"
mkdir "%USERPROFILE%\Desktop\token1"

# Linux/Mac
mkdir ~/Desktop/token
mkdir ~/Desktop/token1
```

7. 验证安装：
   - 确保Chrome浏览器已安装
   - 验证Python环境（3.8+）
   - 检查所有依赖包已安装
   - 确认环境变量已设置
   - 验证目录结构

4. 配置文件说明：
- config.py：包含所有配置项，可以通过环境变量覆盖默认值
- requirements.txt：所需的Python包列表

## 运行程序

1. 运行实时更新程序：
```bash
python real_time_running/real_time_update.py
```

2. 运行价格监控：
```bash
python telegram_price_alert.py
```

3. 运行服务器监控：
```bash
python server_monitoring/server_metrics_collector.py
```

## 文件结构
- real_time_running/：实时数据更新和监控模块
- data_analysis/：数据分析模块
- server_monitoring/：服务器监控模块
- config.py：配置文件
- telegram_price_alert.py：Telegram提醒模块

## 注意事项
1. 首次运行前请确保已设置所有必要的环境变量
2. 确保网络连接正常，可以访问CoinGecko API
3. 建议使用虚拟环境运行程序

## 技术支持
如有问题，请联系技术支持。
