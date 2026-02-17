import streamlit as st
import db
import time

def render_tmdb_config():
    # 1. 加载配置
    # 优先从 session 读取，如果没有则从数据库读取
    if 'cfg_tmdb' not in st.session_state:
        st.session_state.cfg_tmdb = db.load_tmdb_config()
    
    # 方便引用
    cfg = st.session_state.cfg_tmdb

    # 2. 界面布局
    # API 域名
    api_domain = st.text_input(
        "API域名", 
        value=cfg.get('api_domain', 'https://api.tmdb.org'),
        placeholder="例如: https://api.tmdb.org"
    )

    # 图片域名
    image_domain = st.text_input(
        "图片域名", 
        value=cfg.get('image_domain', 'https://image.tmdb.org'),
        placeholder="例如: https://image.tmdb.org"
    )

    # API 密钥 (密码框显示)
    api_key = st.text_input(
        "API密钥", 
        value=cfg.get('api_key', ''),
        type="password",
        placeholder="请输入你的 TMDB API Key v3 Auth"
    )

    # 3. 底部按钮栏
    st.write("---")
    c_save, c_reset, _ = st.columns([1.5, 1.5, 7])
    
    with c_save:
        if st.button("💾 保存配置", type="primary", key="btn_save_tmdb"):
            # 保存到数据库
            db.save_tmdb_config(api_domain, image_domain, api_key)
            
            # 更新 Session
            st.session_state.cfg_tmdb = {
                "api_domain": api_domain,
                "image_domain": image_domain,
                "api_key": api_key
            }
            st.toast("TMDB 配置已保存！", icon="🎉")
    
    with c_reset:
        if st.button("⟳ 重置配置", key="btn_reset_tmdb"):
            # 删除数据库记录
            db.reset_tmdb_config()
            # 清除 Session
            st.session_state.pop('cfg_tmdb', None)
            st.toast("配置已重置为默认值", icon="🗑️")
            time.sleep(0.5)
            st.rerun()