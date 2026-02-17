import streamlit as st
import json
import os
import threading
import time
import lib_quark_strm
import lib_scheduler
import lib_alist
import lib_log

CONFIG_FILE = 'quark_sync_config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)

# --- 后台任务包装器 ---
def background_task_wrapper(mode, src, dst):
    """后台线程执行入口"""
    if mode == 'incremental':
        lib_quark_strm.sync_quark_incremental_stateless(src, dst)
    elif mode == 'full':
        lib_quark_strm.sync_quark_full(src, dst)

def run_sync_task_logic():
    """供调度器调用"""
    cfg = load_config()
    if not cfg.get('src_path') or not cfg.get('dst_path'):
        return
    lib_quark_strm.sync_quark_incremental_stateless(cfg['src_path'], cfg['dst_path'])

def render_page():
    st.header("⏳ 夸克网盘同步配置")
    
    # === 状态检测与自动刷新 ===
    is_running = lib_quark_strm.is_task_running()
    running_task_name = lib_quark_strm.get_running_task_name()
    
    if is_running:
        # 任务运行中：显示警告 + 自动刷新
        st.warning(f"⚠️ 系统正在执行任务：**{running_task_name}**")
        st.info("⏳ 任务运行中，页面将自动刷新监测状态，请稍候...")
        
        # 这里的逻辑是：渲染完页面后，等待 2 秒，然后强制重载
        # 这样就实现了“轮询”效果，一旦任务结束，is_running 变为 False，就会跳出这个循环
        time.sleep(2)
        st.rerun()
    else:
        # 任务空闲：显示正常状态
        st.success("✅ 系统空闲，可以执行新任务。")
    # ========================
    
    cfg = load_config()
    alist_cfg = lib_alist._load_config() or {}
    default_src = alist_cfg.get('quark_mount_path', '/quark')
    
    with st.container(border=True):
        st.subheader("1. 路径配置")
        c1, c2 = st.columns(2)
        with c1:
            src_path = st.text_input("AList 源路径", value=cfg.get('src_path', default_src))
        with c2:
            dst_path = st.text_input("本地保存路径", value=cfg.get('dst_path', '/data/strm/quark'))
            
        st.subheader("2. 定时计划")
        c3, c4 = st.columns([3, 1])
        with c3:
            cron_exp = st.text_input("Cron 表达式", value=cfg.get('cron', '0 */1 * * *'))
        with c4:
            st.write("")
            st.write("")
            enable_task = st.checkbox("启用定时任务", value=cfg.get('enabled', False))
            
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            new_cfg = {'src_path': src_path, 'dst_path': dst_path, 'cron': cron_exp, 'enabled': enable_task}
            save_config(new_cfg)
            if enable_task:
                lib_scheduler.add_quark_job(cron_exp)
                st.success("配置已保存，定时任务已启动")
            else:
                lib_scheduler.remove_quark_job()
                st.warning("定时任务已关闭")

    st.divider()
    
    st.subheader("⚡ 手动后台执行")
    
    col_inc, col_full = st.columns(2)
    
    # --- 按钮 1: 增量 ---
    # disabled=is_running 确保任务运行时按钮不可点
    if col_inc.button("🚀 启动后台增量同步", use_container_width=True, disabled=is_running):
        if not src_path or not dst_path:
            st.error("请先配置路径")
        else:
            t = threading.Thread(target=background_task_wrapper, args=('incremental', src_path, dst_path))
            t.daemon = True
            t.start()
            
            st.toast("🚀 增量任务已启动！")
            time.sleep(0.5) 
            st.rerun() # 立即刷新，进入“is_running”循环

    # --- 按钮 2: 全量 ---
    if col_full.button("🔥 启动后台全量同步", type="secondary", use_container_width=True, disabled=is_running):
        if not src_path or not dst_path:
            st.error("请先配置路径")
        else:
            t = threading.Thread(target=background_task_wrapper, args=('full', src_path, dst_path))
            t.daemon = True
            t.start()
            
            st.toast("🔥 全量任务已启动！")
            time.sleep(0.5)
            st.rerun() # 立即刷新，进入“is_running”循环