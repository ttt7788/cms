import requests
import json
import os
import time
import db

# 115 API 常量
API_FILE_LIST = "https://webapi.115.com/files"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

def _get_cookie():
    """从配置读取 115 Cookie"""
    try:
        cfg = db.load_115_config()
        # 优先读取 cookie_path 指向的文件内容
        cookie_path = cfg.get('cookie_path')
        if cookie_path and os.path.exists(cookie_path):
            with open(cookie_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        # 兼容直接存储的 cookie
        return cfg.get('cookie', '')
    except:
        return ""

def _get_headers():
    return {
        "User-Agent": USER_AGENT,
        "Cookie": _get_cookie(),
        "Content-Type": "application/x-www-form-urlencoded"
    }

def get_files(cid="0", limit=1000):
    """
    获取指定 CID 下的文件列表 (自动翻页)
    """
    headers = _get_headers()
    if not headers["Cookie"]:
        return {"success": False, "msg": "未检测到 Cookie，请先在【账号配置->115网盘】进行登录"}

    all_files = []
    offset = 0
    
    try:
        while True:
            params = {
                "aid": "1",
                "cid": cid,
                "o": "user_ptime", # 按修改时间排序
                "asc": "0",
                "offset": offset,
                "show_dir": "1",
                "limit": limit,
                "snap": "0",
                "natsort": "1",
                "format": "json"
            }
            
            # 调用 115 接口
            resp = requests.get(API_FILE_LIST, params=params, headers=headers, timeout=10)
            data = resp.json()
            
            if not data.get("state"):
                return {"success": False, "msg": data.get("error", "API 请求失败")}
            
            file_list = data.get("data", [])
            if not file_list:
                break
                
            all_files.extend(file_list)
            
            if len(file_list) < limit:
                break
            
            offset += len(file_list)
            time.sleep(0.1) # 轻微延时防止频控

        return {"success": True, "data": all_files}
    except Exception as e:
        return {"success": False, "msg": str(e)}

def get_dir_cid_by_path(path_str):
    """
    (工具) 根据路径字符串反查 CID
    如: "/我的接收/电影" -> "123456"
    """
    path_str = path_str.replace("\\", "/").strip("/")
    if not path_str: return {"success": True, "cid": "0"}
    
    parts = path_str.split("/")
    current_cid = "0"
    
    for part in parts:
        res = get_files(current_cid)
        if not res['success']: return res
        
        found = False
        for item in res['data']:
            # 'fid' 不存在即为文件夹
            if item.get('n') == part and 'fid' not in item:
                current_cid = item.get('cid')
                found = True
                break
        
        if not found:
            return {"success": False, "msg": f"路径不存在: {part}"}
            
    return {"success": True, "cid": current_cid}