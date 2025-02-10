import os
import logging

def fix_log_encoding():
    # 配置日志编码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        encoding='utf-8'  # 设置日志编码为UTF-8
    )
    
    # 修改日志处理器的编码
    for handler in logging.root.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.encoding = 'utf-8'

    # 设置环境变量，确保Python输出使用UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'

if __name__ == "__main__":
    fix_log_encoding() 