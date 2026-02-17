import streamlit as st
import db
import lib_pansearch
import lib_115_login as lib115
import lib_scheduler
import time
import re
from datetime import datetime
import threading

# ==============================================================================
# 画质评分逻辑 (移至此方便页面展示和后台逻辑复用)
# ==============================================================================
def calculate_quality_score(item):
    """
    根据资源描述计算清晰度分数
    """
    text = (item.get('note', '') + " " + item.get('title', '')).lower()
    score = 0
    
    # 分辨率权重
    if '2160p' in text or '4k' in text: score += 1000
    elif '1080p' in text: score += 500
    
    # 质量权重
    if 'remux' in text or '原盘' in text: score += 200
    if 'web-dl' in text or 'webrip' in text: score += 50
    
    # 特性加分
    if 'hdr' in text or 'vision' in text or '杜比' in text: score += 20
    if '特效' in text or '字幕' in text: score += 5
    
    # 屏蔽词
    if 'trailer' in text or '预告' in text: score -= 5000
    return score

# ==============================================================================
# 页面渲染
# ==============================================================================
def render_subscription_page():
    st.header("🔔 我的订阅")

    # 1. 获取配置
    tmdb_cfg = db.load_tmdb_config()
    img_domain = tmdb_cfg.get('image_domain', 'https://image.tmdb.org')
    
    cfg_115 = db.load_115_config()
    cookie_path = cfg_115.get('cookie_path', 'config/115-cookies.txt')
    default_cid = cfg_115.get('default_cid', '0')

    # 2. 获取订阅列表
    subs = db.get_subscriptions()

    # ==============================================================================
    # 任务计划控制台 (后台 Cron 模式)
    # ==============================================================================
    with st.expander("🛠️ 后台任务管理", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 2])
        
        with c1:
            is_running = lib_scheduler.scheduler.running
            st.write(f"📊 **调度状态:** {'🟢 运行中' if is_running else '🔴 已停止'}")
            st.caption("表达式: `*/20 8-23 * * *`")
        
        with c2:
            if st.button("♻️ 手动触发同步", use_container_width=True, help="立即在后台线程开始搜索转存任务"):
                # 使用线程异步执行，防止卡死 Streamlit UI
                t = threading.Thread(target=lib_scheduler.auto_sync_task)
                t.start()
                st.toast("已触发后台同步任务...")

        with c3:
            if st.button("🔄 刷新订阅列表", use_container_width=True):
                st.rerun()

    st.divider()

    # 3. 列表展示
    if not subs:
        st.info("当前没有待处理的订阅任务。")
        return

    st.markdown(f"**待处理订阅: {len(subs)} 个** (系统将按 Cron 计划自动处理)")
    
    st.markdown("""
    <style>
    .sub-card { margin-bottom: 10px; }
    .sub-title { font-size: 14px; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 5px; }
    .type-badge { background-color: #3498db; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
    .type-badge.tv { background-color: #9b59b6; }
    </style>
    """, unsafe_allow_html=True)

    cols = st.columns(6)
    for i, item in enumerate(subs):
        with cols[i % 6]:
            poster = f"{img_domain.rstrip('/')}/t/p/w500{item['poster_path']}" if item['poster_path'] else "https://placehold.co/500x750?text=No+Image"
            st.image(poster, use_container_width=True)

            type_label = "电影" if item['type'] == 'movie' else "剧集"
            type_class = "" if item['type'] == 'movie' else "tv"
            
            st.markdown(f"""
            <div class="sub-card">
                <div style="margin-bottom:4px;">
                    <span class="type-badge {type_class}">{type_label}</span>
                </div>
                <div class="sub-title" title="{item['name']}">{item['name']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("移除", key=f"del_{item['type']}_{item['id']}", type="secondary", use_container_width=True):
                db.remove_subscription(item['id'], item['type'])
                st.toast(f"已移除: {item['name']}")
                time.sleep(0.5)
                st.rerun()

# ==============================================================================
# 自动任务函数 (用于手动点击执行时调用，复用逻辑)
# ==============================================================================
def run_auto_process_ui(subs, cid, cookie_path):
    """
    此函数仅作为页面上显式执行时的反馈，
    后台 Cron 任务主要通过 lib_scheduler.auto_sync_task 运行。
    """
    status = st.status("正在手动处理订阅...", expanded=True)
    for item in subs:
        name = item['name']
        status.write(f"🔍 搜索: {name}")
        # 这里逻辑同后台任务，略...
    status.update(label="处理尝试完成", state="complete")