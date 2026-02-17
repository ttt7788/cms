import streamlit as st
import lib_log
import time
import pandas as pd # 需要 pandas 来优化表格显示

def render_log_page():
    st.header("📜 系统运行日志 (数据库版)")
    
    # === 顶部工具栏 ===
    c1, c2, c3, c4 = st.columns([1.5, 1.5, 2, 2])
    
    with c1:
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()
            
    with c2:
        if st.button("🗑️ 清空", use_container_width=True):
            if lib_log.clear_logs():
                st.toast("✅ 数据库已清空")
                time.sleep(0.5)
                st.rerun()
    
    with c3:
        # 筛选器
        level_filter = st.selectbox("日志等级", ["ALL", "INFO", "WARNING", "ERROR", "DEBUG"], label_visibility="collapsed")
        
    with c4:
        auto_refresh = st.checkbox("⚡ 自动刷新(3s)", value=True)

    st.divider()
    
    # === 分页逻辑 ===
    if 'log_page_index' not in st.session_state:
        st.session_state.log_page_index = 0
        
    PAGE_SIZE = 20 # 每页显示 20 条，不卡顿
    
    # 获取数据
    total_count = lib_log.get_total_logs_count(level_filter)
    logs_data = lib_log.read_logs_db(limit=PAGE_SIZE, offset=st.session_state.log_page_index * PAGE_SIZE, level_filter=level_filter)
    
    # === 表格展示 ===
    if logs_data:
        # 转换为 DataFrame 以便美观展示
        df = pd.DataFrame(logs_data, columns=["ID", "时间", "等级", "内容"])
        
        # 颜色标记
        def highlight_level(val):
            color = 'black'
            if val == 'ERROR': color = 'red'
            elif val == 'WARNING': color = 'orange'
            elif val == 'INFO': color = 'green'
            elif val == 'DEBUG': color = 'gray'
            return f'color: {color}; font-weight: bold'

        # 隐藏 ID 列，应用样式
        st.dataframe(
            df[["时间", "等级", "内容"]].style.applymap(highlight_level, subset=['等级']),
            use_container_width=True,
            hide_index=True,
            height=800 # 固定高度，避免页面抖动
        )
    else:
        st.info("暂无日志数据。")

    # === 底部翻页栏 ===
    c_prev, c_info, c_next = st.columns([1, 2, 1])
    
    with c_prev:
        if st.session_state.log_page_index > 0:
            if st.button("⬅️ 上一页", use_container_width=True):
                st.session_state.log_page_index -= 1
                st.rerun()
                
    with c_info:
        total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
        current_p = st.session_state.log_page_index + 1
        st.markdown(f"<div style='text-align: center; line-height: 32px;'>第 {current_p} / {max(1, total_pages)} 页 (共 {total_count} 条)</div>", unsafe_allow_html=True)
        
    with c_next:
        if (st.session_state.log_page_index + 1) * PAGE_SIZE < total_count:
            if st.button("下一页 ➡️", use_container_width=True):
                st.session_state.log_page_index += 1
                st.rerun()

    # === 自动刷新逻辑 ===
    if auto_refresh:
        time.sleep(3)
        st.rerun()