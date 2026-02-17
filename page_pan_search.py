import streamlit as st
import db
import lib_pansearch
import lib_115_login as lib115
import time

def render_pan_search_page():
    st.header("🔍 资源搜刮")
    
    # [核心优化 1] 初始化状态缓存
    # pan_search_res: 缓存搜索结果，防止刷新丢失
    # transfer_status: 缓存每个文件的转存状态 {url_hash: {'status': bool, 'msg': str}}
    if 'pan_search_res' not in st.session_state:
        st.session_state.pan_search_res = None
    if 'transfer_status' not in st.session_state:
        st.session_state.transfer_status = {}
    
    # 搜索区
    c1, c2 = st.columns([5, 1])
    with c1:
        kw = st.text_input("关键词", placeholder="输入电影/剧集名称...", label_visibility="collapsed")
    with c2:
        go = st.button("搜 索", type="primary", use_container_width=True)

    # 执行搜索
    if go and kw:
        with st.spinner("正在全网搜索资源..."):
            res = lib_pansearch.search(kw)
            st.session_state.pan_search_res = res # 更新搜索结果缓存
            # 搜索新词时，保留之前的转存状态缓存其实是个好特性（提示你以前存过），所以不强制清空 transfer_status
            
    # 渲染结果 (基于缓存)
    if st.session_state.pan_search_res:
        res = st.session_state.pan_search_res
        
        if not res['success']:
            st.error(res['msg'])
        else:
            data = res['data']
            merged = data.get('merged_by_type', {})
            total = data.get('total', 0)
            
            # 仅在刚点击搜索时显示提示
            if go: st.success(f"✅ 搜索完成，共找到 {total} 条结果")
            
            # 读取配置
            cfg_115 = db.load_115_config()
            cid = cfg_115.get('default_cid', '0')
            cookie_path = cfg_115.get('cookie_path')

            if merged:
                # 动态生成 Tabs
                tabs = st.tabs([f"{k.upper()} ({len(v)})" for k, v in merged.items() if v])
                
                for i, (dtype, items) in enumerate(merged.items()):
                    if not items: continue
                    with tabs[i]:
                        for item in items:
                            render_item_card(item, dtype, cid, cookie_path)
            else:
                st.info("未搜刮到相关有效资源")

def render_item_card(item, dtype, cid, cookie_path):
    """渲染单个资源卡片，包含状态自更新逻辑"""
    with st.container(border=True):
        c_info, c_btn = st.columns([5, 1.5])
        
        title = item.get('note') or item.get('title') or '无标题'
        url = item.get('url')
        pwd = item.get('password', '')
        
        # 生成唯一 Key
        item_key = str(hash(url))
        
        with c_info:
            # 标题处理
            display_title = title.replace("<span class='highlight-keyword'>", "**").replace("</span>", "**")
            st.markdown(f"📄 **{display_title}**")
            
            # 元数据
            meta = []
            if item.get('datetime'): meta.append(f"📅 {item['datetime'][:10]}")
            if item.get('source'): meta.append(f"🔗 {item['source']}")
            st.caption(" | ".join(meta))
            
            # 链接与提取码
            if pwd:
                st.code(f"链接: {url}  提取码: {pwd}", language=None)
            else:
                st.caption(f"链接: `{url}`")

            # [核心优化 2] 如果有失败记录，显示在信息栏下方
            status_cache = st.session_state.transfer_status.get(item_key)
            if status_cache and not status_cache['success']:
                st.error(f"上次失败: {status_cache['msg']}")

        with c_btn:
            st.write("") # 占位
            
            if dtype == '115':
                # [核心优化 3] 根据状态动态渲染按钮
                status_cache = st.session_state.transfer_status.get(item_key)
                
                # 情况 A: 已经成功
                if status_cache and status_cache['success']:
                    st.button("✅ 已转存", key=f"btn_ok_{item_key}", disabled=True, use_container_width=True)
                
                # 情况 B: 未操作 或 失败 (允许重试)
                else:
                    btn_label = "💾 存入根目录" if str(cid) == "0" else f"💾 存入 {cid}"
                    
                    if st.button(btn_label, key=f"btn_save_{item_key}", type="primary", use_container_width=True):
                        if not cookie_path:
                            st.error("未配置Cookie")
                        else:
                            # 执行转存
                            handle_transfer(item_key, title, url, pwd, cid, cookie_path)
            
            # 原链接跳转
            st.link_button("🌐 打开链接", url, use_container_width=True)

def handle_transfer(item_key, title, url, pwd, cid, cookie_path):
    """处理转存逻辑并更新状态"""
    with st.spinner("正在提交..."):
        try:
            # 1. 调用接口
            res = lib115.import_115_share(url, pwd, cid=cid, cookie_path=cookie_path)
            
            is_success = res.get('status', False) or res.get('state', False)
            msg = str(res.get('msg', '') or res.get('error_msg', '未知结果'))
            
            # 2. 写入数据库日志
            if hasattr(db, 'add_transfer_log'):
                db.add_transfer_log("115手动", title, url, is_success, msg)
            
            # 3. 更新 Session 状态
            st.session_state.transfer_status[item_key] = {
                'success': is_success,
                'msg': msg
            }
            
            # 4. 强制刷新页面以更新 UI (按钮变绿)
            if is_success:
                st.toast(f"转存成功！\n{title}", icon="✅")
                time.sleep(0.5) # 稍作停顿让用户看到 Toast
                st.rerun()
            else:
                st.toast(f"转存失败: {msg}", icon="❌")
                # 失败时不强制刷新，保留当前页面状态以便查看错误
                
        except Exception as e:
            st.error(f"系统错误: {e}")