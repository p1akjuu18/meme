import os
import shutil
import logging
from datetime import datetime
import schedule
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DataSync')

def sync_files():
    try:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"开始同步 - {current_time}")
        
        # 同步数据文件夹
        data_source = "./data"
        data_backup = f"./backup/data_{current_time}"
        if os.path.exists(data_source):
            shutil.copytree(data_source, data_backup)
            logger.info(f"数据文件夹已同步到: {data_backup}")
            
        # 同步日志文件
        log_files = [
            'data_scheduler.log',
            'sync.log',
            'price_analysis_scheduler.log'
        ]
        
        log_backup = f"./backup/logs_{current_time}"
        os.makedirs(log_backup, exist_ok=True)
        
        for log_file in log_files:
            if os.path.exists(log_file):
                shutil.copy2(log_file, os.path.join(log_backup, log_file))
                logger.info(f"日志文件 {log_file} 已同步")
                
        # 清理旧备份（保留最近7天的）
        cleanup_old_backups()
        
        logger.info("同步完成")
        
    except Exception as e:
        logger.error(f"同步过程出错: {str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")

def cleanup_old_backups():
    """清理7天以前的备份"""
    try:
        backup_dir = "./backup"
        if not os.path.exists(backup_dir):
            return
            
        # 获取所有备份文件夹
        all_backups = []
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path):
                all_backups.append(item_path)
                
        # 按创建时间排序
        all_backups.sort(key=lambda x: os.path.getctime(x), reverse=True)
        
        # 保留最近7天的备份，删除其他的
        if len(all_backups) > 7:
            for old_backup in all_backups[7:]:
                shutil.rmtree(old_backup)
                logger.info(f"已删除旧备份: {old_backup}")
                
    except Exception as e:
        logger.error(f"清理旧备份时出错: {str(e)}")

def init_backup_dir():
    """初始化备份目录"""
    try:
        backup_dir = "./backup"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            logger.info("创建备份目录成功")
    except Exception as e:
        logger.error(f"创建备份目录时出错: {str(e)}")

def main():
    try:
        logger.info("同步服务启动")
        
        # 初始化备份目录
        init_backup_dir()
        
        # 设置定时任务，每6小时运行一次
        schedule.every(6).hours.do(sync_files)
        
        # 程序启动时立即运行一次
        sync_files()
        
        # 持续运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次是否有待运行的任务
            
    except Exception as e:
        logger.error(f"主程序运行出错: {str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 