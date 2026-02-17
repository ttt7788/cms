import streamlit as st
import lib_115_drive
import lib_sync
import time
import os

def render_full_sync_page():
    st.header("🔄 115网盘 -> 本地 STRM 同步")
    st.info("此功能使用 115 原生接口高速扫描目录，在本地生成指向 AList 的 .strm 文件，供 Emby/Plex 完美播放。")
    
    with st.container(border=True):
        st.subheader("1. 115 源目录")
        col_src, col_btn = st.columns([3, 1])
        with col_src:
            src_val = st.text_input("CID 或 文件夹路径", value="0", help="输入 '0' 代表根目录，或输入如 '/我的接收/电影'")
        with col_btn:
            st.write("")
            st.write("")
            # 辅助工具：路径转 CID
            if st.button("🆔 解析路径 CID"):
                if src_val.isdigit():
                    st.toast(f"当前已是 CID: {src_val}")
                else:
                    with st.spinner("正在连接 115 解析路径..."):
                        res = lib_115_drive.get_dir_cid_by_path(src_val)
                        if res['success']:
                            st.success(f"解析成功！CID: {res['cid']}")
                            st.session_state.temp_cid = res['cid'] # 临时存一下
                        else:
                            st.error(f"解析失败: {res['msg']}")

        st.subheader("2. 本地保存位置")
        dst_path = st.text_input("本地目标路径", value="/data/strm/115", help="请填写容器内可写的路径，Emby 需挂载此路径")
        
        st.subheader("3. AList 播放配置")
        c1, c2 = st.columns(2)
        with c1:
            # 自动尝试从 lib_alist 获取配置
            default_host = "http://192.168.1.X:5244"
            alist_host = st.text_input("AList 访问地址", value=default_host, help="Emby/播放器能访问到的 AList 地址")
        with c2:
            alist_mount = st.text_input("115 挂载路径", value="/115", help="在 AList 中 115 网盘的挂载名称，如 /115")

        st.divider()
        
        if st.button("🚀 开始同步生成", type="primary", use_container_width=True):
            # 确定 CID
            final_cid = src_val
            # 如果刚才解析过且输入框没变，或者用户输入的是路径
            if not final_cid.isdigit():
                res = lib_115_drive.get_dir_cid_by_path(final_cid)
                if not res['success']:
                    st.error(f"无法解析路径: {res['msg']}")
                    return
                final_cid = res['cid']

            # 初始化日志区域
            log_container = st.container(border=True, height=300)
            status_text = st.empty()
            progress_bar = st.progress(0, text="准备开始...")
            
            def log_callback(msg):
                log_container.text(msg)
            
            try:
                start_time = time.time()
                status_text.info("🚀 正在高速扫描 115 目录树...")
                
                # 执行同步
                stats = lib_sync.sync_115_to_strm(
                    src_cid=final_cid,
                    local_root_dir=dst_path,
                    alist_host=alist_host,
                    alist_mount=alist_mount,
                    callback=log_callback
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                progress_bar.progress(100, text="同步完成")
                st.balloons()
                
                st.success(f"""
                ✅ **同步完成！** 耗时: {duration:.2f} 秒
                - 📁 扫描目录: {stats['dirs']}
                - 📄 生成文件: {stats['files']}
                - ⏭️ 跳过未变: {stats['skips']}
                - ❌ 错误数量: {stats['errors']}
                """)
                
            except Exception as e:
                st.error(f"发生异常: {str(e)}")

def render_inc_sync_page():
    st.info("增量同步功能开发中，当前请使用全量同步（会自动跳过已存在文件）。")