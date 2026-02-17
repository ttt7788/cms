import streamlit as st
import db
import time
import urllib.request
import urllib.error

def test_proxy_latency(proxy_url):
    """
    测试代理连接延迟
    目标: Google (因为代理通常是为了连通外网)
    """
    target_url = "https://www.google.com"
    
    if not proxy_url:
        return False, "代理地址为空"
    
    # 自动补全 http://
    if not proxy_url.startswith("http"):
        proxy_url = "http://" + proxy_url
        
    try:
        # 配置代理 Handler
        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        # 伪装 User-Agent 防止被直接拦截
        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
        
        start_time = time.time()
        # 设置 5 秒超时
        with opener.open(target_url, timeout=5) as response:
            pass # 只要能打开就算成功
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000
        return True, f"{latency:.0f}ms"
        
    except urllib.error.HTTPError as e:
        # 如果返回 HTTP 错误码 (如 403, 500)，说明连通了服务器，只是页面报错，代理是通的
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        return True, f"{latency:.0f}ms (HTTP {e.code})"
    except Exception as e:
        # 连接超时或被拒绝
        return False, f"连接失败: {str(e)}"

def render_proxy_config():
    # 1. 加载配置
    if 'cfg_proxy' not in st.session_state:
        st.session_state.cfg_proxy = db.load_proxy_config()
    
    cfg = st.session_state.cfg_proxy

    # 2. 界面布局
    st.info("ℹ️ 用于加速访问tmdb、电报")
    
    c1, c2 = st.columns([5, 1])
    with c1:
        proxy_input = st.text_input(
            "http代理", 
            value=cfg.get('http_proxy', ''),
            placeholder="例如: http://192.168.68.200:20171"
        )
    with c2:
        # 为了美观，让按钮和输入框对齐，我们可以在CSS里微调，但这里直接放按钮即可
        if st.button("测试延迟", type="primary"):
            with st.spinner("正在测试代理连接 (目标: google.com)..."):
                success, msg = test_proxy_latency(proxy_input)
            
            if success:
                st.success(f"✅ 测试成功，延迟: {msg}")
            else:
                st.error(f"❌ 测试失败: {msg}")

    # 3. 底部按钮栏
    st.write("---")
    c_save, c_reset, _ = st.columns([1.5, 1.5, 7])
    
    with c_save:
        if st.button("💾 保存配置", type="primary", key="btn_save_proxy"):
            db.save_proxy_config(proxy_input)
            st.session_state.cfg_proxy = {"http_proxy": proxy_input}
            st.toast("代理配置已保存！", icon="🎉")
    
    with c_reset:
        if st.button("⟳ 重置配置", key="btn_reset_proxy"):
            db.reset_proxy_config()
            st.session_state.pop('cfg_proxy', None)
            st.toast("代理配置已重置", icon="🗑️")
            time.sleep(0.5)
            st.rerun()