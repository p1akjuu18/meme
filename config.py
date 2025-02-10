import os

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(ROOT_DIR, "data")

# Token数据目录
TOKEN_FOLDER = os.path.join(DATA_DIR, "token")

# token查询结果文件路径
TOKEN_QUERY_FILE = os.path.join(DATA_DIR, 'token_query_results_filtered.xlsx')

# 创建必要的目录
def ensure_directories():
    """确保所有必要的目录都存在"""
    directories = [
        DATA_DIR,
        TOKEN_FOLDER,
        os.path.join(ROOT_DIR, "logs")
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建目录: {directory}")

# 在导入时自动创建目录
ensure_directories()