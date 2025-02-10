from real_time_running.price_analysis_scheduler import create_scheduler

def your_function():
    try:
        # 创建调度器但不自动启动
        scheduler = create_scheduler(auto_start=False)
        
        # 只运行一次分析
        scheduler.run_once()
        
        # 或者如果需要启动完整的调度循环
        # scheduler.run()
        
    except Exception as e:
        print(f"运行价格分析时出错: {e}") 