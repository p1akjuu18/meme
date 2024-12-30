import os
import glob
from datetime import datetime
import subprocess

def get_latest_file(pattern):
    """获取指定模式的最新文件"""
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    files = glob.glob(os.path.join(desktop_path, pattern))
    if not files:
        return None
    return max(files, key=os.path.getctime)

def main():
    print(f"开始执行数据处理流程 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        # 步骤1: 运行数据采集
        print("\n=== 步骤1: 运行数据采集程序 ===")
        # 直接运行run_gmgn_data.py
        try:
            subprocess.run(['python', 'run_gmgn_data.py'], check=True)
            print("数据采集完成")
        except subprocess.CalledProcessError as e:
            print(f"数据采集失败: {str(e)}")
            return
        
        # 获取run_gmgn_data.py生成的最新文件
        latest_json = get_latest_file("json_data_*.json")
        latest_excel = get_latest_file("html_table_data_*.xlsx")
        
        if not latest_json or not latest_excel:
            print("未找到必要的数据文件，程序终止")
            return
            
        print(f"\n采集的数据文件:")
        print(f"JSON文件: {latest_json}")
        print(f"Excel文件: {latest_excel}")
            
        # 步骤2: 处理JSON数据
        print("\n=== 步骤2: 处理JSON数据 ===")
        try:
            env = os.environ.copy()
            env['JSON_INPUT_FILE'] = latest_json
            subprocess.run(['python', 'process_json.py'], env=env, check=True)
            print("JSON数据处理完成")
        except subprocess.CalledProcessError as e:
            print(f"处理JSON数据时出错: {str(e)}")
            return
        
        # 步骤3: 处理Excel数据
        print("\n=== 步骤3: 处理Excel数据 ===")
        try:
            env = os.environ.copy()
            env['EXCEL_INPUT_FILE'] = latest_excel
            subprocess.run(['python', 'process_excel.py'], env=env, check=True)
            print("Excel数据处理完成")
        except subprocess.CalledProcessError as e:
            print(f"处理Excel数据时出错: {str(e)}")
            return
        
        print("\n数据处理流程完成")
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        return False

if __name__ == "__main__":
    main() 