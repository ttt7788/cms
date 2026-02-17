import json
import urllib.request
import urllib.parse
import urllib.error
import db

def search(keyword):
    """
    调用盘搜 API (POST /api/search)
    """
    cfg = db.load_pansearch_config()
    api_url = cfg.get('api_url', 'http://192.168.68.200:8080')
    
    if not api_url.startswith("http"):
        api_url = "http://" + api_url
    endpoint = f"{api_url.rstrip('/')}/api/search"

    data = {"kw": keyword}
    json_data = json.dumps(data).encode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    token = cfg.get('api_token')
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        req = urllib.request.Request(endpoint, data=json_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # --- 核心修复：同时兼容 code=0 和 code=200 ---
            code = result.get('code')
            if code == 0 or code == 200:
                # 成功！返回 data 部分
                # 注意：API返回的数据结构是 result['data']['merged_by_type']
                return {"success": True, "data": result.get('data', {})}
            
            # 某些非标接口直接返回数据列表的情况
            elif 'results' in result or 'merged_by_type' in result:
                return {"success": True, "data": result}
                
            else:
                # 真正的错误
                return {"success": False, "msg": f"API返回错误 (Code {code}): {result.get('message', '未知错误')}"}
                
    except urllib.error.URLError as e:
        return {"success": False, "msg": f"连接失败: {e.reason}. 请检查地址 {api_url}"}
    except Exception as e:
        return {"success": False, "msg": f"请求异常: {str(e)}"}