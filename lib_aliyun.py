import json
import time
import requests
import db
import hashlib
import uuid

# 尝试导入 ecdsa 库 (必须安装: pip install ecdsa)
try:
    import ecdsa
    from ecdsa import SECP256k1, SigningKey
    from ecdsa.util import sigencode_string
    HAS_ECDSA = True
except ImportError:
    HAS_ECDSA = False

# --- 阿里云盘 App 接口配置 (Personal) ---
# 注意：AList 源码中使用的是这个 App ID
APP_ID = "5dde4e1bdf9e4966b387ba58f4b3fdc3"
AUTH_URL = "https://auth.alipan.com/v2/account/token"
API_BASE = "https://api.alipan.com/v2"
API_V3 = "https://api.alipan.com/adrive/v3"
PASSPORT_BASE = "https://passport.aliyundrive.com/newlogin/qrcode"

# --- 1. 签名算法模块 (ECDSA secp256k1) ---
def get_device_id(user_id):
    """根据 UserID 生成固定的 DeviceID"""
    return hashlib.sha256(user_id.encode()).hexdigest()

def get_signature_data(user_id, device_id, private_key_hex):
    """计算 X-Signature 签名"""
    if not HAS_ECDSA: return None, None
    try:
        # 还原私钥
        sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
        vk = sk.verifying_key
        pub_key_hex = vk.to_string("uncompressed").hex()
        
        # 构造签名原文: appId:deviceId:userId:nonce
        data = f"{APP_ID}:{device_id}:{user_id}:0"
        hash_bytes = hashlib.sha256(data.encode()).digest()
        
        # 签名
        sig = sk.sign_digest(hash_bytes, sigencode=sigencode_string)
        # 拼接 00 作为 recovery id (简易模拟)
        signature_hex = sig.hex() + "00"
        
        return signature_hex, pub_key_hex
    except Exception as e:
        print(f"Signature Error: {e}")
        return None, None

def _create_session(access_token, user_id):
    """注册设备会话 (解决接口返回空数据的问题)"""
    if not HAS_ECDSA: return False
    
    device_id = get_device_id(user_id)
    sig, pub_key = get_signature_data(user_id, device_id, device_id)
    if not sig: return False
    
    # 注册接口需要完整的 App Headers
    headers = {
        "Content-Type": "application/json",
        "X-Canary": "client=Android,app=adrive,version=v4.1.0",
        "X-Device-Id": device_id,
        "X-Signature": sig,
        "Authorization": f"Bearer\t{access_token}" # 注意制表符
    }
    
    payload = {
        "deviceName": "samsung",
        "modelName": "SM-G9810",
        "nonce": 0,
        "pubKey": pub_key,
        "refreshToken": db.load_aliyun_config().get('refresh_token')
    }
    
    try:
        # 发送注册请求，忽略返回值
        requests.post("https://api.alipan.com/users/v1/users/device/create_session", json=payload, headers=headers, timeout=5)
        return True
    except:
        return False

# --- 2. 基础请求头构造 ---
def _get_app_headers(access_token=""):
    """业务接口 (如获取文件) 需要伪装成 Android App"""
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://www.alipan.com/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G9810) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 Mobile Safari/537.36",
        "X-Canary": "client=Android,app=adrive,version=v4.1.0"
    }
    if access_token:
        # 这里的 Token 后面加 \t 是 AList 的核心 Trick
        headers["Authorization"] = f"Bearer\t{access_token}"
    return headers

def _sign_headers(headers, user_id):
    """给请求头附加签名"""
    if not HAS_ECDSA: return headers
    device_id = get_device_id(user_id)
    sig, _ = get_signature_data(user_id, device_id, device_id)
    if sig:
        headers["X-Device-Id"] = device_id
        headers["X-Signature"] = sig
        headers["x-request-id"] = str(uuid.uuid4())
    return headers

# --- 3. 核心修复：纯净刷新逻辑 ---
def refreshToken():
    """
    [关键] 刷新 Token 必须使用纯净请求头
    不要带 X-Canary 或 X-Device-Id，否则 auth.alipan.com 会报 InvalidParameter.ClientId
    """
    cfg = db.load_aliyun_config()
    rt = cfg.get('refresh_token')
    if not rt: return False, "未配置 Refresh Token"
    
    try:
        # 仅包含最基础的 Headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        payload = {
            "refresh_token": rt,
            "grant_type": "refresh_token"
        }
        
        # 请求 auth.alipan.com
        resp = requests.post(AUTH_URL, json=payload, headers=headers, timeout=15)
        data = resp.json()
        
        if 'access_token' in data:
            db.save_aliyun_config(data['refresh_token'], data['access_token'], 7200)
            return True, "刷新成功"
        else:
            # 透传错误信息
            return False, f"刷新失败: {data.get('code')} - {data.get('message')}"
            
    except Exception as e:
        return False, f"网络异常: {str(e)}"

# --- 4. 业务接口 ---
def get_drive_info():
    if not HAS_ECDSA:
        return {"success": False, "msg": "缺少依赖: 请在终端运行 pip install ecdsa"}

    cfg = db.load_aliyun_config()
    at = cfg.get('access_token')
    
    # 1. 如果没有 Access Token，先刷新
    if not at:
        ok, msg = refreshToken()
        if not ok: return {"success": False, "msg": msg}
        at = db.load_aliyun_config().get('access_token')

    try:
        # 2. 获取 UserID (使用 App Headers 尝试)
        headers = _get_app_headers(at)
        user_resp = requests.post(f"{API_BASE}/user/get", json={}, headers=headers, timeout=10).json()
        
        # 如果 Token 失效，尝试刷新并重试
        if user_resp.get('code') == 'AccessTokenInvalid':
            refreshToken()
            at = db.load_aliyun_config().get('access_token')
            headers = _get_app_headers(at)
            user_resp = requests.post(f"{API_BASE}/user/get", json={}, headers=headers, timeout=10).json()

        user_id = user_resp.get('user_id')
        if not user_id:
            return {"success": False, "msg": f"获取用户信息失败: {user_resp.get('message')}"}

        # 3. 注册 App Session (关键步骤，否则无法获取文件)
        _create_session(at, user_id)
        
        # 4. 获取 Drive 信息 (带签名)
        signed_headers = _sign_headers(headers, user_id)
        drive_resp = requests.post(f"{API_V3}/user/drive/get_default_drive", json={}, headers=signed_headers).json()
        
        return {
            "success": True, 
            "nick_name": user_resp.get('nick_name'), 
            "user_id": user_id,
            "drive_id": drive_resp.get('drive_id'),
            "resource_id": user_resp.get('resource_drive_id'),
            "backup_id": user_resp.get('default_drive_id')
        }
    except Exception as e: return {"success": False, "msg": str(e)}

def get_file_list(parent_file_id="root"):
    """获取文件列表 (自动签名，解决为空问题)"""
    # 1. 先获取用户信息以计算签名
    info = get_drive_info()
    if not info['success']: return info
    
    user_id = info['user_id']
    import streamlit as st
    # 优先使用 Session 中选定的 Drive，否则用 Backup Drive (扫码登录默认盘)
    drive_id = st.session_state.get('ali_curr_drive') or info['backup_id'] or info['drive_id']

    at = db.load_aliyun_config().get('access_token')
    headers = _sign_headers(_get_app_headers(at), user_id)
    
    files = []
    marker = ""
    try:
        while True:
            payload = {
                "drive_id": drive_id,
                "parent_file_id": parent_file_id,
                "limit": 100,
                "marker": marker,
                "order_by": "updated_at",
                "order_direction": "DESC",
                "url_expire_sec": 14400 # 链接有效期 4小时
            }
            resp = requests.post(f"{API_BASE}/file/list", json=payload, headers=headers)
            data = resp.json()
            
            if 'items' not in data:
                return {"success": False, "msg": f"API Error: {data.get('message')}", "raw": data}

            items = data.get('items', [])
            files.extend(items)
            
            marker = data.get('next_marker', "")
            if not marker: break
            
        return {"success": True, "items": files, "drive_id": drive_id}
    except Exception as e: return {"success": False, "msg": str(e)}

# --- 扫码逻辑 (通用) ---
def get_qrcode_info():
    ts = int(time.time() * 1000)
    try:
        resp = requests.get(f"{PASSPORT_BASE}/generate.do?appName=aliyun_drive&fromSite=52&_ksTS={ts}").json()
        data = resp['content']['data']
        return {"success": True, "t": data['t'], "ck": data['ck'], "codeContent": data['codeContent']}
    except Exception as e: return {"success": False, "msg": str(e)}

def check_qrcode_status(t, ck):
    ts = int(time.time() * 1000)
    try:
        resp = requests.post(f"{PASSPORT_BASE}/query.do?appName=aliyun_drive&fromSite=52&_ksTS={ts}", data={"t": t, "ck": ck}).json()
        content = resp.get('content', {}).get('data', {})
        if content.get('qrCodeStatus') == 'CONFIRMED':
            import base64
            rt = json.loads(base64.b64decode(content['bizExt']).decode('utf-8'))['pds_login_result']['refreshToken']
            return {"success": True, "status": "CONFIRMED", "refresh_token": rt}
        return {"success": True, "status": content.get('qrCodeStatus')}
    except Exception as e: return {"success": False, "msg": str(e)}