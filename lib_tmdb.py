import urllib.request
import urllib.parse
import json
import db
import time
import streamlit as st 

# 电影类型
GENRES_MOVIE = {
    28: "动作", 12: "冒险", 16: "动画", 35: "喜剧", 80: "犯罪",
    99: "纪录", 18: "剧情", 10751: "家庭", 14: "奇幻", 36: "历史",
    27: "恐怖", 10402: "音乐", 9648: "悬疑", 10749: "爱情", 878: "科幻",
    10770: "电视电影", 53: "惊悚", 10752: "战争", 37: "西部"
}

# 剧集类型
GENRES_TV = {
    10759: "动作冒险", 16: "动画", 35: "喜剧", 80: "犯罪", 99: "纪录",
    18: "剧情", 10751: "家庭", 10762: "儿童", 9648: "悬疑", 10763: "新闻",
    10764: "真人秀", 10765: "科幻/奇幻", 10766: "肥皂剧", 10767: "脱口秀",
    10768: "战争/政治", 37: "西部"
}

def _get_opener():
    proxy_cfg = db.load_proxy_config()
    proxy_url = proxy_cfg.get('http_proxy')
    handlers = []
    if proxy_url and proxy_url.startswith('http'):
        handlers.append(urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url}))
    opener = urllib.request.build_opener(*handlers)
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
    return opener

def _fetch_tmdb(endpoint, params=None):
    tmdb_cfg = db.load_tmdb_config()
    api_key = tmdb_cfg.get('api_key')
    base_url = tmdb_cfg.get('api_domain', 'https://api.tmdb.org')
    
    if not api_key: return {"success": False, "msg": "未配置API密钥"}
    if params is None: params = {}
    
    params['api_key'] = api_key
    params['language'] = 'zh-CN'
    
    query = urllib.parse.urlencode(params)
    url = f"{base_url.rstrip('/')}/3/{endpoint.lstrip('/')}?{query}"
    
    try:
        opener = _get_opener()
        with opener.open(url, timeout=10) as response:
            return {"success": True, "data": json.loads(response.read().decode('utf-8'))}
    except Exception as e:
        return {"success": False, "msg": str(e)}

# --- 电影接口 ---
def fetch_popular_movies(page=1): return _fetch_tmdb('movie/popular', {'page': page})
def search_movies(query, page=1): return _fetch_tmdb('search/movie', {'query': query, 'page': page})
def discover_movies(year=None, genre=None, region=None, page=1):
    p = {'page': page, 'sort_by': 'popularity.desc'}
    if year: p['primary_release_year'] = year
    if genre: p['with_genres'] = genre
    if region: p['region'] = region
    return _fetch_tmdb('discover/movie', p)

# --- 剧集接口 ---
def fetch_popular_tv(page=1): return _fetch_tmdb('tv/popular', {'page': page})
def search_tv(query, page=1): return _fetch_tmdb('search/tv', {'query': query, 'page': page})
def discover_tv(year=None, genre=None, page=1):
    p = {'page': page, 'sort_by': 'popularity.desc'}
    if year: p['first_air_date_year'] = year
    if genre: p['with_genres'] = genre
    return _fetch_tmdb('discover/tv', p)

# --- 循环采集逻辑 ---
def sync_data_loop(media_type="movie", keyword=None, year=None, genre=None, region=None, max_pages=50):
    """通用循环采集函数：自动翻页入库"""
    
    # 1. 确定初始 API 函数和参数
    if media_type == "movie":
        save_func = db.save_movies
        if keyword:
            fetch_func = search_movies; kwargs = {'query': keyword}
        elif year or genre or region:
            gid = None
            if genre and genre != "全部":
                for k, v in GENRES_MOVIE.items(): 
                    if v == genre: gid = k; break
            fetch_func = discover_movies
            kwargs = {'year': year if year!="全部" else None, 'genre': gid, 'region': region if region!="全部" else None}
        else:
            fetch_func = fetch_popular_movies; kwargs = {}
    else: # tv
        save_func = db.save_tv_shows
        if keyword:
            fetch_func = search_tv; kwargs = {'query': keyword}
        elif year or genre:
            gid = None
            if genre and genre != "全部":
                for k, v in GENRES_TV.items(): 
                    if v == genre: gid = k; break
            fetch_func = discover_tv
            kwargs = {'year': year if year!="全部" else None, 'genre': gid}
        else:
            fetch_func = fetch_popular_tv; kwargs = {}

    # 2. 循环采集
    total_items = 0
    current_page = 1
    progress_bar = st.progress(0, text="准备开始采集...")
    status_text = st.empty()
    
    try:
        while current_page <= max_pages:
            status_text.text(f"正在采集第 {current_page} 页...")
            res = fetch_func(page=current_page, **kwargs)
            
            if not res['success']: return False, f"第{current_page}页失败: {res['msg']}"
            
            data = res['data']
            results = data.get('results', [])
            total_pages = data.get('total_pages', 1)
            
            if not results: break 
            save_func(results)
            total_items += len(results)
            
            p = min(current_page / min(total_pages, max_pages), 1.0)
            progress_bar.progress(p, text=f"已采集 {total_items} 条 (页码: {current_page}/{min(total_pages, max_pages)})")
            
            if current_page >= total_pages: break
            current_page += 1
            time.sleep(0.2)
            
        progress_bar.empty(); status_text.empty()
        return True, f"采集完成！共获取 {total_items} 条数据。"
        
    except Exception as e:
        return False, f"采集异常: {str(e)}"