import os

def find_file_path(filename):
    current_path = os.getcwd()  # 获取当前工作目录
    print(f"当前文件夹位置: {current_path}")
    
    # 搜索 static/trade_tracker 文件夹
    if os.path.exists("static/trade_tracker"):
        full_path = os.path.abspath("static/trade_tracker")
        print(f"找到项目文件夹: {full_path}")

find_file_path("app.py") 