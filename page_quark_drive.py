import streamlit as st
import lib_alist
import os

def render_quark_drive_page():
    st.header("🐿️ 夸克网盘文件 (AList)")
    
    # 1. 获取配置的挂载路径
    cfg = lib_alist._load_config()
    # 如果没配置，默认路径为 /quark
    mount_path = cfg.get('quark_mount_path', '/quark')
    
    # 2. 初始化路径栈
    if 'quark_alist_stack' not in st.session_state:
        st.session_state.quark_alist_stack = []
        
    # 3. 计算当前完整路径
    current_rel_path = "/".join(st.session_state.quark_alist_stack)
    full_path = os.path.join(mount_path, current_rel_path).replace("\\", "/")
    
    # 4. 顶部导航栏
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.session_state.quark_alist_stack:
            if st.button("⬅️ 返回上一级", use_container_width=True):
                st.session_state.quark_alist_stack.pop()
                st.rerun()
        else:
            st.button("🚫 根目录", disabled=True, use_container_width=True)
    with c2:
        st.info(f"当前路径: `{full_path}`")
    
    st.divider()
    
    # 5. 调用 AList 获取文件列表
    with st.spinner(f"正在从 AList 加载..."):
        res = lib_alist.fs_list(full_path)
        
    # 6. 处理错误
    if not res['success']:
        st.error(f"加载失败: {res['msg']}")
        if "token" in str(res.get('msg', '')).lower() or "未配置" in str(res.get('msg', '')):
            st.warning("请检查：\n1. AList 是否已启动\n2. 【账号配置 -> AList连接】是否已连接")
        return
        
    items = res['data'].get('content', [])
    if not items:
        st.info("📂 空文件夹")
        return
        
    # 7. 渲染列表
    for item in items:
        with st.container(border=True):
            c1, c2, c3 = st.columns([0.5, 4, 1.5])
            is_dir = item['is_dir']
            name = item['name']
            
            with c1: st.write("📁" if is_dir else "📄")
            with c2: 
                st.write(f"**{name}**")
                if not is_dir:
                    size = item.get('size', 0)
                    st.caption(f"{size/1024/1024:.2f} MB")
            
            with c3:
                if is_dir:
                    if st.button("进入", key=f"qk_go_{name}"):
                        st.session_state.quark_alist_stack.append(name)
                        st.rerun()
                else:
                    if st.button("下载/预览", key=f"qk_dl_{name}"):
                        # 获取文件直链
                        file_res = lib_alist.fs_get(os.path.join(full_path, name).replace("\\", "/"))
                        if file_res['success']:
                            url = file_res['data'].get('raw_url')
                            st.success("获取成功！")
                            st.link_button("点击打开", url)
                        else:
                            st.error(f"获取链接失败: {file_res['msg']}")