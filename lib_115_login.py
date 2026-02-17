import json
import time
import os
import re
from urllib.parse import urlencode
from urllib.request import urlopen, Request

# --- 全局设置 ---
_LAST_REQ = 0.0
_API_INTERVAL = 3.0

def set_api_interval(s): global _API_INTERVAL; _API_INTERVAL = float(s)

# --- User-Agent 模拟池 ---
def _get_ua(app_type="web"):
    if app_type in ['ios', 'ipad', 'mac']:
        return "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 115/30.0.0"
    elif app_type in ['android', 'tv']:
        return "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.193 Mobile Safari/537.36 115/30.0.0"
    elif app_type in ['qandroid']:
        return "Mozilla/5.0 (Linux; Android 13; 22081212C Build/TP1A.220905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 XWEB/1160065 MMWEBSDK/20231202 MMWEBID/8888 MicroMessenger/8.0.47.2560(0x28002F35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64"
    else:
        # 默认 Web UA
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def _get_h(c=None, app="web"):
    h = {
        "User-Agent": _get_ua(app),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    if c: h["Cookie"] = c
    return h

def _request(url, data=None, headers=None, method=None):
    global _LAST_REQ
    elapsed = time.time() - _LAST_REQ
    if elapsed < _API_INTERVAL: time.sleep(_API_INTERVAL - elapsed)
    req = Request(url, data=data, headers=headers or {}, method=method)
    with urlopen(req) as r:
        _LAST_REQ = time.time()
        # 某些接口返回是非标准JSON，这里做一个简单的容错
        resp_text = r.read().decode('utf-8')
        try:
            return json.loads(resp_text)
        except:
            # 如果解析失败，可能是jsonp或者其他格式，尝试清洗
            if "(" in resp_text and ")" in resp_text:
                try:
                    return json.loads(resp_text[resp_text.find("(")+1:resp_text.rfind(")")])
                except: pass
            return {"state": False, "msg": "API响应解析失败", "raw": resp_text}

# --- 登录相关 ---
def get_qrcode_token(app="web"):
    base_url = f"https://qrcodeapi.115.com/api/1.0/{app}/1.0/token/"
    return _request(base_url, headers=_get_h(app=app))

def get_qrcode_image_url(uid): 
    return f"https://qrcodeapi.115.com/api/1.0/mac/1.0/qrcode?uid={uid}"

def get_qrcode_status(p): 
    return _request(f"https://qrcodeapi.115.com/get/status/?{urlencode(p)}", headers=_get_h(app="web"))

def post_login_result(uid, app="web"): 
    url = f"https://passportapi.115.com/app/1.0/{app}/1.0/login/qrcode/"
    data = urlencode({"app": app, "account": uid}).encode()
    return _request(url, data=data, method="POST", headers=_get_h(app=app))

# --- 工具函数 ---
def format_cookie_string(d): return "; ".join(f"{k}={v}" for k, v in d.items())
def save_cookie_to_file(s, p): 
    if os.path.dirname(p): os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f: f.write(s)

# --- 业务接口 (核心修复区域) ---

def get_user_info_by_file(p, app="web"):
    """
    检测 Cookie 有效性
    """
    if not os.path.exists(p): return {"status": False, "msg": "Cookie文件不存在"}
    with open(p, 'r') as f: c = f.read().strip()
    
    # 策略 1: 使用 my.115.com 导航接口 (最稳健)
    try:
        res = _request("https://my.115.com/?ct=ajax&ac=nav", headers=_get_h(c, "web"))
        # 这个接口成功时，data 里面会有 user_id
        if res and res.get('data') and 'user_id' in res['data']:
            return {"status": True, "user_id": res['data']['user_id'], "cookie": c}
    except: pass

    # 策略 2: 使用 webapi index_info (备用)
    try:
        res = _request("https://webapi.115.com/files/index_info", headers=_get_h(c, "web"))
        if res.get("state") and res.get('data') and 'user_id' in res['data']:
            return {"status": True, "user_id": res['data']['user_id'], "cookie": c}
        
        # 如果策略2能通但不含user_id，说明cookie可能仅仅是部分有效，或者需要更新
        if res.get("state"):
             return {"status": False, "msg": f"登录部分有效，但无法获取UID，请尝试【Web-网页版】重新扫码。Debug: {list(res.get('data',{}).keys())}"}
             
    except Exception as e:
        return {"status": False, "msg": f"请求异常: {str(e)}"}

    return {"status": False, "msg": "Cookie无效或已过期，请重新扫码"}

def import_115_share(link, pwd, cid="0", cookie_path="config/115-cookies.txt"):
    m = re.search(r'/s/([a-z0-9]+)', link)
    if not m: return {"status": False, "msg": "链接格式错误"}
    
    uinfo = get_user_info_by_file(cookie_path)
    if not uinfo['status']: return uinfo
    
    payload = urlencode({"user_id": uinfo['user_id'], "share_code": m.group(1), "receive_code": pwd, "cid": cid}).encode()
    res = _request("https://webapi.115.com/share/receive", data=payload, method="POST", headers=_get_h(uinfo['cookie'], "web"))
    return {"status": res.get("state"), "msg": res.get("error_msg", "成功" if res.get("state") else "失败")}

def upload_sha1(name, size, sha1, cid="0", cookie_path="config/115-cookies.txt"):
    uinfo = get_user_info_by_file(cookie_path)
    if not uinfo['status']: return uinfo
    api = "https://uplb.115.com/3.0/sampleinit_offline.php"
    payload = urlencode({"filename": name, "filesize": size, "preid": sha1, "fileid": sha1, "target": f"U_0_{cid}"}).encode()
    res = _request(api, data=payload, method="POST", headers=_get_h(uinfo['cookie'], "web"))
    return {"status": res.get("state"), "msg": "秒传成功" if res.get("state") else res.get("msg", "失败")}

def add_task_url(url, cookie_path="config/115-cookies.txt"):
    uinfo = get_user_info_by_file(cookie_path)
    if not uinfo['status']: return uinfo
    api = "https://115.com/web/lixian/?ct=lixian&ac=add_task_url"
    payload = urlencode({"url": url, "uid": uinfo['user_id']}).encode()
    res = _request(api, data=payload, method="POST", headers=_get_h(uinfo['cookie'], "web"))
    return {"status": res.get("state"), "msg": res.get("error_msg", "提交成功" if res.get("state") else "失败")}