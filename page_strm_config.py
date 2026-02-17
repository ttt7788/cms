import streamlit as st
import json
import os

# 配置文件路径
STRM_CONFIG_FILE = 'strm_config.json'

def load_strm_config():
    """加载 STRM 配置"""
    if os.path.exists(STRM_CONFIG_FILE):
        try:
            with open(STRM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def save_strm_config(cfg):
    """保存 STRM 配置"""
    with open(STRM_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)

def render_strm_config():
    """渲染配置界面"""
    st.markdown("### 📺 STRM 播放路径配置")
    st.info("设置 STRM 文件内容的**路径前缀**。支持 HTTP/WebDAV 链接，也支持本地盘符路径。")
    
    cfg = load_strm_config()
    default_url = "http://192.168.1.5:5244"
    
    with st.container(border=True):
        url_prefix = st.text_input(
            "全局路径前缀 / 播放域名", 
            value=cfg.get('url_prefix', default_url),
            placeholder="例如: http://192.168.68.200:9527 或 Z:/CloudDrive",
            help="STRM 内容 = 前缀 + 挂载目录 + 文件相对路径"
        )
        
        # 增加一个编码选项，因为本地路径(Z:/...)通常不需要URL编码，而HTTP需要
        need_encode = st.checkbox("启用 URL 编码", value=cfg.get('need_encode', True), 
                                  help="如果是 HTTP/WebDAV 链接建议开启；如果是本地盘符路径(Z:/)建议关闭")
        
        st.caption(f"📝 预览格式: `{url_prefix.rstrip('/')}/115/电影/Avatar.mkv`")
        
        if st.button("💾 保存配置"):
            cfg['url_prefix'] = url_prefix.rstrip('/')
            cfg['need_encode'] = need_encode
            save_strm_config(cfg)
            st.toast("配置已保存")