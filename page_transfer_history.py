import streamlit as st
import pandas as pd
import db

def render_transfer_history_page():
    st.header("📜 转存记录")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c2:
        status_filter = st.selectbox("状态筛选", ["全部", "成功", "失败"], index=0)
    with c3:
        if st.button("🗑️ 清空所有记录", type="secondary"):
            db.clear_transfer_logs(); st.rerun()

    s_val = 1 if status_filter == "成功" else 0 if status_filter == "失败" else None
    logs = db.get_transfer_logs(limit=100, status_filter=s_val)
    
    if not logs: st.info("暂无记录"); return

    df = pd.DataFrame(logs)
    df = df.rename(columns={"id":"ID", "type":"来源", "title":"资源名", "status":"状态", "time":"时间", "msg":"反馈", "link":"链接"})
    df["状态"] = df["状态"].apply(lambda x: "✅ 成功" if x else "❌ 失败")
    
    st.dataframe(df, column_config={"链接": st.column_config.LinkColumn("链接"), "时间": st.column_config.DatetimeColumn("时间", format="Y-M-D HH:mm:ss")}, use_container_width=True, hide_index=True)