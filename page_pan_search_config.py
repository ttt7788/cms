import streamlit as st
import db

def render_pan_search_config():
    st.subheader("🔍 盘搜源配置")
    
    # 加载现有配置
    cfg = db.load_pansearch_config()
    
    with st.container(border=True):
        st.info("💡 这里配置你的聚合搜索后端地址 (例如: xiaoya / pan-search-api)。")
        
        api_url = st.text_input(
            "API 地址", 
            value=cfg.get('api_url', 'http://127.0.0.1:8080'), 
            placeholder="http://192.168.1.5:8080",
            help="聚合搜索服务的访问地址，请务必带上 http://"
        )
        
        api_token = st.text_input(
            "API Token (可选)", 
            value=cfg.get('api_token', ''), 
            type="password", 
            help="如果你的搜索服务开启了鉴权，请在此填入 Token/密钥"
        )
        
        st.write("")
        if st.button("💾 保存盘搜配置", type="primary"):
            if api_url.endswith('/'): 
                api_url = api_url[:-1] # 去除末尾斜杠
            
            db.save_pansearch_config(api_url, api_token)
            st.toast("盘搜源配置已保存！", icon="✅")