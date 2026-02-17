import streamlit as st
import pandas as pd
import time

def render_sync_records_page():
    st.header("📜 数据同步记录")
    
    # 模拟数据，后续从 db 读取
    data = [
        {"id": "JOB_001", "type": "全量同步", "src": "/quark/电影", "dst": "115/备份", "status": "✅ 完成", "time": "2023-10-27 10:00", "files": 120},
        {"id": "JOB_002", "type": "增量同步", "src": "/quark/剧集", "dst": "115/追更", "status": "🔄 进行中", "time": "2023-10-27 12:30", "files": 5},
        {"id": "JOB_003", "type": "全量同步", "src": "/aliyun/资源", "dst": "115/资源", "status": "❌ 失败", "time": "2023-10-26 09:15", "files": 0},
    ]
    
    # 筛选区
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        st.selectbox("任务状态", ["全部", "进行中", "完成", "失败"])
    with c2:
        st.text_input("搜索任务ID/路径")
    with c3:
        st.write("")
        st.write("")
        st.button("🔄 刷新")

    # 表格展示
    df = pd.DataFrame(data)
    st.dataframe(
        df,
        column_config={
            "id": "任务ID",
            "type": "类型",
            "src": "源路径",
            "dst": "目标路径",
            "status": "状态",
            "time": "开始时间",
            "files": "文件数"
        },
        use_container_width=True,
        hide_index=True
    )