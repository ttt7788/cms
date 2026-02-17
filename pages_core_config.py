import streamlit as st
import streamlit_antd_components as sac

def render_core_config():
    # 1. 顶部 Tab 导航
    tabs = sac.tabs([
        sac.TabsItem('115账号'),
        sac.TabsItem('STRM配置'),
        sac.TabsItem('TMDB配置'),
        sac.TabsItem('代理配置'),
        sac.TabsItem('EMBY入库刷新'),
        sac.TabsItem('EMBY入库通知'),
    ], size='sm', align='start')

    # --- 通用组件：保存与重置按钮 ---
    def render_action_buttons():
        st.write("---")
        c1, c2, _ = st.columns([1, 1, 6])
        with c1:
            st.button("💾 保存配置", type="primary", use_container_width=True)
        with c2:
            st.button("⟳ 重置配置", type="secondary", use_container_width=True)

    # --- 样式调整：让输入框和按钮对齐 ---
    st.markdown("""
    <style>
    div[data-testid="column"] { display: flex; align-items: center; } 
    /* 调整一些间距 */
    .stAlert { padding: 0.5rem 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Tab 1: 115账号
    # -------------------------------------------------------------------------
    if tabs == '115账号':
        st.info("ℹ️ 请先在115手机APP里打开生活事件记录，然后清空；然后再开始使用CMS")
        
        # Cookie 路径 + 检测按钮
        c1, c2 = st.columns([5, 1])
        with c1:
            st.text_input(":red[*] cookie文件路径", value="/config/115-cookies.txt", help="cookie存放的绝对路径")
        with c2:
            st.button("✔ 检测可用性", type="primary")
            
        # 模拟检测成功的绿色提示
        st.success("✔ 账号: 网老奸巨滑，容量: 48.34TB / 49.12TB")

        # 设备类型 + 二维码登录
        c1, c2 = st.columns([5, 1])
        with c1:
            st.selectbox(":red[*] cookie对应设备类型", ["D1 - 115生活(iOS端)", "Android", "Web"], help="选择对应的设备标识")
        with c2:
            st.button("▞ 二维码登录", type="primary")

        # OpenAPI 开关
        st.write(":red[*] 是否启用OPENAPI")
        sac.segmented(
            items=[sac.SegmentedItem(label='启用'), sac.SegmentedItem(label='禁用')],
            index=1, size='sm'
        )

        st.text_input("115开放平台AppID", placeholder="请填写自己申请的115开放平台AppID")
        
        c1, c2 = st.columns([5, 1])
        with c1:
            st.number_input("API请求间隔", value=3.0, step=0.1)
        with c2:
            st.write("秒")

        st.warning("⚡ 设置API请求间隔可以减少风控概率")
        
        render_action_buttons()

    # -------------------------------------------------------------------------
    # Tab 2: STRM配置
    # -------------------------------------------------------------------------
    elif tabs == 'STRM配置':
        st.text_input(":red[*] strm直连地址", value="http://192.168.68.200:9527")
        
        st.write("strm直连格式")
        sac.segmented(
            items=['pick_code', 'pick_code_name'],
            index=1, size='sm'
        )

        st.write("是否保留文件后缀")
        sac.segmented(
            items=['是', '否'],
            index=0, size='sm'
        )

        st.write("strm文件本地存在时")
        sac.segmented(
            items=['覆盖生成', '直接跳过'],
            index=0, size='sm'
        )

        st.text_input("strm生成示例", value="http://192.168.68.200:9527/d/abchrb6.../钢铁侠.mkv", disabled=True)
        
        render_action_buttons()

    # -------------------------------------------------------------------------
    # Tab 3: TMDB配置
    # -------------------------------------------------------------------------
    elif tabs == 'TMDB配置':
        st.text_input("API域名", value="https://api.tmdb.org")
        st.text_input("图片域名", value="https://image.tmdb.org")
        st.text_input("API密钥", type="password", value="123456")
        
        st.write("语言")
        sac.segmented(
            items=['中文', '英文'],
            index=0, size='sm'
        )
        
        render_action_buttons()

    # -------------------------------------------------------------------------
    # Tab 4: 代理配置
    # -------------------------------------------------------------------------
    elif tabs == '代理配置':
        st.info("ℹ️ 用于加速访问tmdb、电报")
        
        c1, c2 = st.columns([5, 1])
        with c1:
            st.text_input("http代理", value="http://192.168.68.200:20171")
        with c2:
            st.button("测试延迟", type="primary")
            
        render_action_buttons()

    # -------------------------------------------------------------------------
    # Tab 5: EMBY入库刷新
    # -------------------------------------------------------------------------
    elif tabs == 'EMBY入库刷新':
        st.info("ℹ️ 用于strm生成时通知emby刷新入库；不是必须，你开emby的实时监控也一样...")
        
        c1, c2 = st.columns([1, 4])
        with c1:
            st.write("路径替换规则")
        with c2:
            st.text_input("rule", label_visibility="collapsed", placeholder="格式: 源路径#目标路径")
            st.success("用于将cms的路径转为emby的路径，为空代表不需要转换")
            
        c1, c2 = st.columns([1, 4])
        with c1:
            st.write("路径风格")
        with c2:
            sac.segmented(['Unix风格', 'Windows风格'], size='sm')

        c1, c2 = st.columns([1, 4])
        with c1:
            st.write("路径转换测试")
        with c2:
            st.text_input("test", label_visibility="collapsed", placeholder="在这里输入一个在cms中的路径")
            st.success("在这里输入一个在cms中的路径，下面这个路径如果是emby的就代表你填的路径替换规则是对的")

        c1, c2 = st.columns([1, 4])
        with c1:
            st.write("状态")
        with c2:
            sac.switch(label='', value=True, align='start', size='lg') # 使用switch模拟勾选框

        render_action_buttons()

    # -------------------------------------------------------------------------
    # Tab 6: EMBY入库通知
    # -------------------------------------------------------------------------
    elif tabs == 'EMBY入库通知':
        st.markdown("**在emby入库成功时进行消息通知**; Webhooks URL: `http://172.17.0.1:9527/...`")
        
        # 模拟图片展示 (你可以替换为真实的图片路径)
        st.image("https://placehold.co/800x400/png?text=Emby+Webhook+Settings", caption="Emby消息通知配置示例")
        
        st.markdown("---")
        st.markdown("如果需要开启emby删除时，同步删除云盘里的资源，需要神医助手开启通知系统增强...")
        st.image("https://placehold.co/800x400/png?text=Emby+Delete+Settings", caption="Emby同步删除云盘文件示例")
        
        render_action_buttons()