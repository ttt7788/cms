import streamlit as st
import streamlit_antd_components as sac
import time

# --- 1. 核心库 ---
import db
import lib_scheduler
import lib_log # 新增

# --- 2. 功能模块 ---
try:
    import page_movie
    import page_tv
    import page_subs
    import page_pan_search
    import page_transfer_add
    import page_transfer_history
    import page_account
    import page_tmdb_config
    import page_proxy_config
    import page_pan_search_config
    # 同步模块
    import page_strm_config
    import page_sync_115
    import page_quark_sync_config
    import page_logs # 新增日志页面
except ImportError: pass

# --- 初始化 ---
if 'sys_init' not in st.session_state:
    try:
        lib_scheduler.start_scheduler()
    except: pass
    st.session_state.sys_init = True

st.set_page_config(layout="wide", page_title="CMS控制台", page_icon="📂")
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e9ecef; } 
    .stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 核心配置渲染 ---
def render_core_config():
    st.header("▎核心配置")
    tabs = sac.tabs([
        sac.TabsItem('计划任务', icon='clock'),
        sac.TabsItem('盘搜配置', icon='search'),
        sac.TabsItem('TMDB配置', icon='film'),
        sac.TabsItem('STRM配置', icon='play-btn'),
        sac.TabsItem('代理配置', icon='globe')
    ], size='sm', align='start', color='blue')

    if tabs == '计划任务':
        st.info("💡 全局转存任务")
        cur_cron = db.load_scheduler_config()
        cron_in = st.text_input("Cron 表达式", value=cur_cron)
        if st.button("💾 更新计划"):
            db.save_scheduler_config(cron_in)
            lib_scheduler.update_job()
            st.success("更新成功")
            
    elif tabs == 'STRM配置':
        if 'page_strm_config' in globals(): page_strm_config.render_strm_config()
    elif tabs == 'TMDB配置': page_tmdb_config.render_tmdb_config()
    elif tabs == '盘搜配置': page_pan_search_config.render_pan_search_config()
    elif tabs == '代理配置': page_proxy_config.render_proxy_config()

# --- 菜单结构 ---
with st.sidebar:
    st.title("📂 CMS控制台")
    
    menu = sac.menu([
        # 1. 账号配置
        sac.MenuItem('账号配置', icon='person-vcard', children=[
            sac.MenuItem('AList连接', icon='link'),
            sac.MenuItem('115网盘', icon='hdd'),
            sac.MenuItem('夸克网盘', icon='box-seam')
        ]),
        
        # 2. 数据同步
        sac.MenuItem('数据同步', icon='arrow-repeat', children=[
            sac.MenuItem('115网盘', icon='hdd', children=[
                 sac.MenuItem('115全量同步', icon='cloud-arrow-up'),
            ]),
            sac.MenuItem('夸克网盘', icon='box-seam', children=[
                 sac.MenuItem('夸克增量配置', icon='clock-history'), 
            ]),
        ]),

        # 3. 资源推荐
        sac.MenuItem('热门推荐', icon='fire', children=[
            sac.MenuItem('电影'), sac.MenuItem('剧集')
        ]),
        
        # 4. 我的订阅
        sac.MenuItem('我的订阅', icon='bell', children=[
            sac.MenuItem('当前订阅'), sac.MenuItem('订阅源管理', children=[sac.MenuItem('源搜索 (盘搜)')])
        ]),
        
        # 5. 转存下载
        sac.MenuItem('转存下载', icon='download', children=[
            sac.MenuItem('任务添加', icon='plus-circle'), sac.MenuItem('转存记录', icon='clock-history')
        ]),
        
        # 6. 日志与设置 (新增系统日志)
        sac.MenuItem('系统管理', icon='pc-display', children=[
            sac.MenuItem('系统日志', icon='file-earmark-text'), # 新增入口
            sac.MenuItem('核心配置', icon='gear-wide-connected')
        ]),
        
    ], index=0, open_all=True)

# --- 路由 ---
if menu == "AList连接": page_account.render_alist_connection_page()
elif menu == "115网盘": page_account.render_115_page()
elif menu == "夸克网盘": page_account.render_quark_page()

# 同步
elif menu == "115全量同步":
    if 'page_sync_115' in globals(): page_sync_115.render_full_sync_page()
elif menu == "夸克增量配置":
    if 'page_quark_sync_config' in globals(): page_quark_sync_config.render_page()

# 日志
elif menu == "系统日志":
    if 'page_logs' in globals(): page_logs.render_log_page()

# 其他
elif menu == "电影": page_movie.render_movie_page()
elif menu == "剧集": page_tv.render_tv_page()
elif menu == "当前订阅": page_subs.render_subscription_page()
elif menu == "源搜索 (盘搜)": page_pan_search.render_pan_search_page()
elif menu == "任务添加": page_transfer_add.render_transfer_add_page()
elif menu == "转存记录": page_transfer_history.render_transfer_history_page()
elif menu == "核心配置": render_core_config()
else: st.info(f"🚧 {menu}")