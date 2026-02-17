import streamlit as st
import lib_alist
import lib_115_login as lib115
import db
import time

# --- AList 连接配置 (夸克依赖此连接) ---
def render_alist_connection_page():
    st.header("🔗 AList 连接配置")
    st.info("对接 AList 服务，主要用于夸克网盘的挂载和浏览。")
    
    # 读取配置
    cfg = lib_alist._load_config()
    
    with st.container(border=True):
        url = st.text_input("AList 地址", value=cfg.get('url', 'http://127.0.0.1:5244'), placeholder="http://ip:port")
        c1, c2 = st.columns(2)
        with c1:
            user = st.text_input("用户名", value=cfg.get('username', 'admin'))
        with c2:
            pwd = st.text_input("密码", value=cfg.get('password', ''), type="password")
            
        if st.button("🔌 连接并保存", type="primary", use_container_width=True):
            with st.spinner("正在登录..."):
                res = lib_alist.login(url, user, pwd)
                if res['success']:
                    st.success("✅ 连接成功！Token 已自动保存。")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ 连接失败: {res['msg']}")

# --- 115 原生配置 (保留) ---
def render_115_page():
    st.header("🅿️ 115网盘配置")
    cfg = db.load_115_config()
    
    device_map = {
        "F1 - 115生活 (Android端)": "android",
        "F3 - 115 (Android端)": "android",
        "D1 - 115生活 (iOS端)": "ios",
        "D3 - 115 (iOS端)": "ios",
        "H3 - 115 (iPad端)": "ios",
        "R1 - 115生活 (微信小程序)": "qandroid", 
        "R2 - 115生活 (支付宝小程序)": "qandroid"
    }

    with st.container(border=True):
        st.subheader("基础设置")
        dev_options = list(device_map.keys())
        curr_dev = cfg.get('device_type')
        default_idx = dev_options.index(curr_dev) if curr_dev in dev_options else 0
        
        c1, c2 = st.columns([3, 1])
        with c1: 
            cp = st.text_input("Cookie文件路径", value=cfg.get('cookie_path'), help="Docker映射路径")
        with c2:
            st.write("")
            st.write("")
            if st.button("🔍 检测有效性", key="chk_115", use_container_width=True):
                res = lib115.get_user_info_by_file(cp, app="web")
                if res['status']: 
                    st.success(f"有效！ID: {res.get('user_id')}")
                else: 
                    st.error(f"失败: {res['msg']}")

        dt = st.selectbox("登录设备模拟", dev_options, index=default_idx)
        cid = st.text_input("默认转存目录ID (CID)", value=cfg.get('default_cid', '0'))
        ai = st.number_input("API请求间隔 (秒)", value=cfg.get('api_interval', 3.0))

    # 115 扫码逻辑
    with st.expander("📱 115 扫码登录"):
        app_code = device_map.get(dt, "android")
        c_qr, c_info = st.columns([1, 2])
        
        if st.button(f"获取 115 二维码 ({app_code})"):
            try:
                token_res = lib115.get_qrcode_token(app=app_code)
                if token_res and 'data' in token_res:
                    st.session_state.qr115_uid = token_res['data']['uid']
                    st.session_state.qr115_app = app_code
                    st.session_state.qr115_dev = dt
                    st.rerun()
            except Exception as e: st.error(f"获取失败: {e}")

        if 'qr115_uid' in st.session_state:
            with c_qr:
                st.image(lib115.get_qrcode_image_url(st.session_state.qr115_uid), width=200)
            with c_info:
                st.info(f"请使用 115 App 扫码。\n当前模拟: **{st.session_state.qr115_dev}**")
                if st.button("我已扫码 (115)"):
                    res = lib115.post_login_result(st.session_state.qr115_uid, app=st.session_state.qr115_app)
                    if res.get('state'):
                        lib115.save_cookie_to_file(lib115.format_cookie_string(res['data']['cookie']), cp)
                        db.save_115_config(cp, st.session_state.qr115_dev, ai, cid)
                        st.success("登录成功！")
                        del st.session_state.qr115_uid
                        st.rerun()
                    else:
                        st.error(f"未完成: {res.get('msg')}")

    if st.button("💾 保存 115 配置", type="primary"):
        db.save_115_config(cp, dt, ai, cid)
        lib115.set_api_interval(ai)
        st.toast("配置已保存", icon="✅")

# --- 夸克网盘 (通过 AList) ---
def render_quark_page():
    st.header("🐿️ 夸克网盘配置 (AList)")
    cfg = lib_alist._load_config()
    
    with st.container(border=True):
        st.write("请配置夸克网盘在 AList 中的挂载路径 (例如 `/quark`)")
        mount_path = st.text_input("挂载路径", value=cfg.get('quark_mount_path', '/quark'))
        
        if st.button("💾 保存路径"):
            cfg['quark_mount_path'] = mount_path
            lib_alist._save_config(cfg)
            st.toast("保存成功")