import streamlit as st
import lib_alist
import db
import os

def render_quark_drive_page():
    st.header("🐿️ 夸克网盘文件 (Via AList)")
    
    try:
        cfg = db.load_quark_config()
        base_mount_path = cfg.get('mount_path', '/quark')
    except:
        st.error("请先在【账号管理 -> 夸克网盘】中配置 AList 挂载路径")
        return

    if 'quark_alist_path' not in st.session_state:
        st.session_state.quark_alist_path = []

    rel_path = "/".join([p['name'] for p in st.session_state.quark_alist_path])
    full_path = os.path.join(base_mount_path, rel_path).replace("\\", "/")
    
    c1, c2 = st.columns([1, 5])
    with c1:
        if len(st.session_state.quark_alist_path) > 0:
            if st.button("⬅️ 返回上级"):
                st.session_state.quark_alist_path.pop()
                st.rerun()
        else:
            st.button("🚫 根目录", disabled=True)
    with c2:
        st.caption(f"当前位置: `{full_path}`")

    st.divider()

    with st.spinner("从 AList 加载中..."):
        res = lib_alist.fs_list(full_path)
    
    if not res['success']:
        st.error(f"加载失败: {res['msg']}")
        return

    content = res['data'].get('content', [])
    if not content:
        st.info("空文件夹")
        return

    for item in content:
        with st.container(border=True):
            c_icon, c_name, c_act = st.columns([0.5, 4, 1.5])
            is_dir = item['is_dir']
            name = item['name']
            
            with c_icon: st.write("📁" if is_dir else "📄")
            with c_name: 
                st.write(f"**{name}**")
                if not is_dir: st.caption(f"Size: {item.get('size', 0)/1024/1024:.2f} MB")
            
            with c_act:
                if is_dir:
                    if st.button("进入", key=f"qk_go_{name}"):
                        st.session_state.quark_alist_path.append({"name": name})
                        st.rerun()
                else:
                    if st.button("获取链接", key=f"qk_get_{name}"):
                        file_res = lib_alist.fs_get(os.path.join(full_path, name).replace("\\", "/"))
                        if file_res['success']:
                            st.link_button("下载 / 预览", file_res['data'].get('raw_url'))
                        else:
                            st.error(file_res['msg'])