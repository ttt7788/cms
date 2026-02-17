import streamlit as st
import lib_alist
import db
import os

def render_aliyun_drive_page():
    st.header("☁️ 阿里云盘文件 (Via AList)")
    
    # 获取配置的挂载路径
    try:
        cfg = db.load_aliyun_config()
        base_mount_path = cfg.get('mount_path', '/aliyun')
    except:
        st.error("请先在【账号管理 -> 阿里云盘】中配置 AList 挂载路径")
        return

    # 初始化路径栈
    if 'ali_alist_path' not in st.session_state:
        st.session_state.ali_alist_path = [] # 相对路径栈

    # 计算当前的完整 AList 路径
    # 如果栈为空，就是 base_mount_path
    # 如果栈不为空，则是 base_mount_path + / + sub_path
    rel_path = "/".join([p['name'] for p in st.session_state.ali_alist_path])
    full_path = os.path.join(base_mount_path, rel_path).replace("\\", "/")
    
    # 顶部导航
    c1, c2 = st.columns([1, 5])
    with c1:
        if len(st.session_state.ali_alist_path) > 0:
            if st.button("⬅️ 返回上级"):
                st.session_state.ali_alist_path.pop()
                st.rerun()
        else:
            st.button("🚫 根目录", disabled=True)
    with c2:
        st.caption(f"当前位置: `{full_path}`")

    st.divider()

    # 获取列表
    with st.spinner("从 AList 加载中..."):
        res = lib_alist.fs_list(full_path, page=1, per_page=0) # 0 表示不分页，全列出
    
    if not res['success']:
        st.error(f"加载失败: {res['msg']}")
        if "Token" in str(res['msg']):
            st.warning("请检查 AList 连接状态")
        return

    content = res['data'].get('content', [])
    if not content:
        st.info("空文件夹")
        return

    # 渲染列表
    for item in content:
        with st.container(border=True):
            c_icon, c_name, c_act = st.columns([0.5, 4, 1.5])
            
            is_dir = item['is_dir']
            name = item['name']
            
            with c_icon:
                st.write("📁" if is_dir else "📄")
            
            with c_name:
                st.write(f"**{name}**")
                if not is_dir:
                    size = item.get('size', 0)
                    if size > 1024**3: size_str = f"{size/1024**3:.2f} GB"
                    else: size_str = f"{size/1024**2:.2f} MB"
                    st.caption(f"{item.get('modified', '')} | {size_str}")
            
            with c_act:
                if is_dir:
                    if st.button("进入", key=f"ali_go_{name}"):
                        st.session_state.ali_alist_path.append({"name": name})
                        st.rerun()
                else:
                    # 对于文件，可以获取下载直链
                    if st.button("获取链接", key=f"ali_get_{name}"):
                        file_res = lib_alist.fs_get(os.path.join(full_path, name).replace("\\", "/"))
                        if file_res['success']:
                            raw_url = file_res['data'].get('raw_url')
                            st.success("获取成功")
                            st.code(raw_url)
                            st.link_button("下载 / 预览", raw_url)
                        else:
                            st.error(file_res['msg'])