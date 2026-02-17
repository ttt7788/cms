from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
import db
# 引入夸克配置页面中的逻辑函数
# 注意：这里需要延迟导入或放在函数内部，避免循环引用，或者我们把逻辑单独放一个文件
# 为了简单，我们在 add_quark_job 里动态导入

scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        # 1. 启动原有系统任务 (如果有)
        try:
            cron_str = db.load_scheduler_config()
            if cron_str:
                update_job() # 这是原有的转存任务
        except: pass
        
        # 2. 启动夸克同步任务 (如果有)
        try:
            import page_quark_sync_config
            cfg = page_quark_sync_config.load_config()
            if cfg.get('enabled') and cfg.get('cron'):
                add_quark_job(cfg['cron'])
        except Exception as e:
            print(f"初始化夸克任务失败: {e}")

        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

# --- 原有转存任务 ---
def _transfer_job():
    print("Executing transfer job...")
    import lib_transfer
    lib_transfer.auto_transfer_task()

def update_job():
    cron_str = db.load_scheduler_config()
    try:
        scheduler.remove_job('main_transfer_job')
    except: pass
    
    if cron_str:
        try:
            scheduler.add_job(_transfer_job, CronTrigger.from_crontab(cron_str), id='main_transfer_job')
            return True, f"计划任务已更新: {cron_str}"
        except Exception as e:
            return False, f"Cron表达式错误: {e}"
    return True, "计划任务已移除"

# --- 新增：夸克同步任务 ---
def _quark_sync_wrapper():
    # 包装器，确保运行时导入，防止循环依赖
    import page_quark_sync_config
    page_quark_sync_config.run_sync_task_logic()

def add_quark_job(cron_exp):
    """添加或更新夸克同步任务"""
    job_id = 'quark_sync_job'
    
    # 先移除旧的
    try:
        scheduler.remove_job(job_id)
    except: pass
    
    try:
        scheduler.add_job(_quark_sync_wrapper, CronTrigger.from_crontab(cron_exp), id=job_id)
        print(f"夸克定时任务已添加: {cron_exp}")
        return True
    except Exception as e:
        print(f"添加夸克任务失败: {e}")
        return False

def remove_quark_job():
    try:
        scheduler.remove_job('quark_sync_job')
        print("夸克定时任务已移除")
    except: pass