import requests
import json
import os

CONFIG_FILE = 'alist_config.json'

def _load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def _save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)

def login(url, username, password):
    """登录 AList 获取 Token"""
    url = url.rstrip('/')
    try:
        resp = requests.post(f"{url}/api/auth/login", json={"username": username, "password": password}, timeout=10)
        data = resp.json()
        if data.get('code') == 200:
            token = data['data']['token']
            cfg = _load_config()
            cfg.update({'url': url, 'username': username, 'password': password, 'token': token})
            _save_config(cfg)
            return {"success": True, "token": token}
        return {"success": False, "msg": data.get('message', '未知错误')}
    except Exception as e:
        return {"success": False, "msg": str(e)}

def fs_list(mount_path, page=1, per_page=0, refresh=False):
    """获取文件列表 (带自动重连)"""
    cfg = _load_config()
    base_url = cfg.get('url')
    token = cfg.get('token')
    
    if not base_url or not token:
        return {"success": False, "msg": "未配置 AList，请先连接"}
    
    headers = {"Authorization": token}
    payload = {"path": mount_path, "page": page, "per_page": per_page, "refresh": refresh}
    
    try:
        resp = requests.post(f"{base_url}/api/fs/list", json=payload, headers=headers, timeout=20)
        data = resp.json()
        
        if data.get('code') == 200:
            return {"success": True, "data": data['data']}
        elif data.get('code') == 401:
            # 自动重试
            res = login(cfg.get('url'), cfg.get('username'), cfg.get('password'))
            if res['success']:
                headers['Authorization'] = res['token']
                resp = requests.post(f"{base_url}/api/fs/list", json=payload, headers=headers, timeout=20)
                return {"success": True, "data": resp.json().get('data')}
        
        return {"success": False, "msg": data.get('message')}
    except Exception as e:
        return {"success": False, "msg": str(e)}

def fs_get(path):
    """获取文件详情"""
    cfg = _load_config()
    headers = {"Authorization": cfg.get('token')}
    try:
        resp = requests.post(f"{cfg.get('url')}/api/fs/get", json={"path": path}, headers=headers, timeout=10)
        data = resp.json()
        return {"success": True, "data": data['data']} if data.get('code') == 200 else {"success": False, "msg": data.get('message')}
    except Exception as e: return {"success": False, "msg": str(e)}