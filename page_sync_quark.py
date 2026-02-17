import streamlit as st
import lib_quark_strm
import page_strm_config
import lib_alist
import time
import os

def render_sync_page():
    st.header("🔄 夸克网盘 -> STRM (增量/全量)")
    st.info("基于 AList 挂载路径进行扫描。全量模式扫描所有文件；增量模式仅处理变动文件。")

    strm_cfg = page_strm_config.load_strm_config()
    prefix = strm_cfg.get('url_prefix', '未配置')
    if prefix == '未配置':
        st.error("请先在【核心配置 -> STRM配置】中设置播放地址前缀！")
        return
    else:
        st.caption(f"当前全局前缀: `{prefix}`")

    alist_cfg = lib_alist._load_config()
    default_mount = alist_cfg.get('quark_mount_path', '/quark')

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            src_path = st.text_input("1. AList 源路径", value=default_mount, help="例如 /quark 或 /quark/剧集")
        with c2:
            dst_path = st.text_input("2. 本地保存路径", value="/data/strm/quark")

        st.write("3. 同步模式")
        col_full, col_inc = st.columns(2)
        
        do_full = col_full.button("🚀 全量同步 (重置缓存)", type="primary", use_container_width=True)
        do_inc = col_inc.button("⏳ 增量同步 (基于缓存)", use_container_width=True)

    if do_full or do_inc:
        mode = 'full' if do_full else 'incremental'
        log_box = st.empty()
        progress = st.progress(0, text="初始化中...")
        
        def log_callback(msg):
            log_box.caption(msg)

        try:
            start_time = time.time()
            log_callback(f"正在开始 {mode} 同步...")
            
            stats = lib_quark_strm.sync_quark_to_strm(
                src_root=src_path,
                local_dst=dst_path,
                mode=mode,
                callback=log_callback
            )
            
            duration = time.time() - start_time
            progress.progress(100, text="完成")
            
            st.success(f"""
            ### ✅ 同步完成
            - **耗时**: {duration:.2f} 秒
            - **新增/更新**: {stats['added']}
            - **跳过(未变)**: {stats['skipped']}
            - **错误**: {stats['errors']}
            """)
        except Exception as e:
            st.error(f"同步出错: {str(e)}")