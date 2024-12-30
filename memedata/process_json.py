import pandas as pd
import json
import os

# 获取用户桌面路径
desktop_path = os.path.expanduser("~/Desktop")

# 从环境变量获取输入文件路径，如果没有则使用默认值
file_path = os.getenv('JSON_INPUT_FILE', os.path.join(desktop_path, "json_data20241222.json"))
output_path = file_path.replace('.json', '.xlsx')

# Load the JSON data
with open(file_path, 'r') as file:
    data = json.load(file)

# Define the fields to extract
fields = [
    "twitter_bind", "twitter_fans_num", "twitter_username", "twitter_name", "name","address",
    "sol_balance", "pnl", "pnl_7d", "pnl_30d", "realized_profit_7d", "realized_profit_30d",
    "winrate", "all_pnl", "total_profit_pnl", "buy_30d", "sell_30d", "buy_7d", "sell_7d",
    "token_num", "profit_num", "pnl_lt_minus_dot5_num", "pnl_minus_dot5_0x_num", "pnl_lt_2x_num",
    "pnl_2x_5x_num", "pnl_gt_5x_num", "tags"
]

# Extract relevant data
extracted_data = []
for address, details in data.items():
    address_info = details.get("props", {}).get("pageProps", {}).get("addressInfo", {})
    row = {field: address_info.get(field, None) for field in fields}
    extracted_data.append(row)

# Convert to DataFrame
df = pd.DataFrame(extracted_data)

# Save to Excel
df.to_excel(output_path, index=False, sheet_name="Extracted Data")

print(f"数据已成功保存到: {output_path}") 