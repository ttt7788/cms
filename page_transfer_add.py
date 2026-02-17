import streamlit as st
import db
import lib_transfer

def render_transfer_add_page():
    st.header("📥 任务添加")
    
    cfg = db.load_115_config()
    cid = cfg.get('default_cid', '0')
    cookie_path = cfg.get('cookie_path')

    st.info(f"📍 转存目标: 115 目录 ID `[{cid}]`")

    with st.container(border=True):
        raw_text = st.text_area(
            "粘贴文本", 
            placeholder="支持：115分享链接、磁力链接(magnet)、电驴(ed2k)、阿里云盘分享...",
            height=300, 
            label_visibility="collapsed"
        )
        
        c1, c2 = st.columns([1, 4])
        with c1:
            run = st.button("🚀 立即转存", type="primary", use_container_width=True)
        with c2:
            st.caption("系统将自动提取文本中包含的所有支持链接。")

    if run and raw_text:
        if not cookie_path:
            st.error("请先在【账号管理 -> 115网盘】中配置 Cookie 路径")
            return

        with st.status("正在解析并提交...", expanded=True) as status:
            results = lib_transfer.identify_and_transfer(raw_text, cid, cookie_path)
            
            if not results:
                status.update(label="⚠️ 未发现任何有效任务", state="error")
            else:
                for r in results:
                    icon = "✅" if r['status'] else "❌"
                    status.write(f"{icon} **[{r['type']}]** {r['msg']} | `{r['link']}`")
                    
                    # [新增] 自动写入数据库日志
                    db.add_transfer_log(
                        log_type="手动批量",
                        title=f"手动添加 - {r['type']}",
                        link=r['link'],
                        status=r['status'],
                        message=r['msg']
                    )
                
                status.update(label=f"任务处理结束，共提交 {len(results)} 个任务", state="complete")
                if any(r['status'] for r in results):
                    st.balloons()