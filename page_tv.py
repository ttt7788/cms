import streamlit as st
import db
import lib_tmdb
import time
import math

def render_tv_page():
    if 'tv_page_index' not in st.session_state: st.session_state.tv_page_index = 1
    tmdb_cfg = db.load_tmdb_config()
    if not tmdb_cfg.get('api_key'): st.warning("⚠️ 未配置API密钥"); st.stop()
    img_domain = tmdb_cfg.get('image_domain', 'https://image.tmdb.org')

    with st.expander("📡 数据采集 (TMDB API)", expanded=False):
        c1, c2, c3 = st.columns([2, 2, 3])
        with c1: 
            if st.button("🚀 更新热门"): 
                with st.spinner("采集..."): s, m = lib_tmdb.sync_data_loop("tv", max_pages=5); st.success(m) if s else st.error(m); time.sleep(1); st.rerun()
        with c2:
            if st.button("📥 深度采集"): 
                with st.spinner("采集..."): s, m = lib_tmdb.sync_data_loop("tv", max_pages=50); st.success(m) if s else st.error(m); time.sleep(1); st.rerun()
        with c3:
            if st.button("🔍 按条件采集", type="secondary"):
                kw=st.session_state.get('tv_kw',''); yr=st.session_state.get('tv_year','全部'); gr=st.session_state.get('tv_genre','全部')
                with st.spinner("采集..."): s, m = lib_tmdb.sync_data_loop("tv", keyword=kw, year=yr if yr!='全部' else None, genre=gr if gr!='全部' else None, max_pages=10); st.success(m) if s else st.error(m); time.sleep(1); st.rerun()

    st.markdown("### 💾 剧集库")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1, 1, 3, 1])
        with c1: st.selectbox("类型", ["全部"] + list(lib_tmdb.GENRES_TV.values()), key="tv_genre")
        with c2: st.selectbox("年份", ["全部"] + [str(y) for y in range(2026, 1990, -1)], key="tv_year")
        with c3: keyword = st.text_input("搜索本地", placeholder="剧集名...", key="tv_kw")
        with c4: 
            if st.button("查询", type="primary", use_container_width=True): st.session_state.tv_page_index=1; st.rerun()

    PAGE_SIZE = 24
    total_count = db.get_tv_count(keyword=keyword)
    total_pages = math.ceil(total_count / PAGE_SIZE) if total_count > 0 else 1
    if st.session_state.tv_page_index > total_pages: st.session_state.tv_page_index = total_pages
    current = st.session_state.tv_page_index; offset = (current - 1) * PAGE_SIZE
    shows = db.get_tv_shows(limit=PAGE_SIZE, offset=offset, keyword=keyword)
    
    if not shows: st.info("暂无数据。")
    else:
        st.markdown(f"**共 {total_count} 条，第 {current} / {total_pages} 页**")
        st.markdown("""<style>.tv-card{margin-bottom:10px;}.tv-title{font-size:14px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:5px;}.rating-badge{background:#222;color:#f1c40f;padding:2px 6px;border-radius:4px;font-size:12px;font-weight:bold;}</style>""", unsafe_allow_html=True)
        
        cols = st.columns(6)
        for i, t in enumerate(shows):
            with cols[i % 6]:
                poster = f"{img_domain.rstrip('/')}/t/p/w500{t['poster_path']}" if t['poster_path'] else "https://placehold.co/500x750?text=No+Image"
                st.image(poster, use_container_width=True)
                
                st.markdown(f"""<div class="tv-card"><div style="display:flex;justify-content:space-between;align-items:center;"><span class="rating-badge">★ {round(t['vote_average'],1)}</span><span style="color:#e74c3c;font-size:12px;">🔥 {int(t['popularity'])}</span></div><div class="tv-title" title="{t['name']}">{t['name']}</div><div style="font-size:12px;color:#666;">{t['first_air_date'][:4] if t['first_air_date'] else ''}</div></div>""", unsafe_allow_html=True)
                
                # --- 订阅按钮逻辑 ---
                is_sub = db.check_is_subscribed(t['id'], 'tv')
                if is_sub:
                    st.button("已订阅", key=f"sub_t_{t['id']}", disabled=True, use_container_width=True)
                else:
                    if st.button("➕ 订阅", key=f"unsub_t_{t['id']}", type="primary", use_container_width=True):
                        db.add_subscription(t['id'], 'tv', t['name'], t['poster_path'])
                        st.toast(f"已订阅: {t['name']}", icon="✅")
                        time.sleep(0.5)
                        st.rerun()

        c_prev, c_space, c_next = st.columns([1, 8, 1])
        with c_prev:
            if st.button("◀ 上一页", disabled=(current <= 1)): st.session_state.tv_page_index -= 1; st.rerun()
        with c_next:
            if st.button("下一页 ▶", disabled=(current >= total_pages)): st.session_state.tv_page_index += 1; st.rerun()