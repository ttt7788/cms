import re
import lib_115_login as lib115

def identify_and_transfer(raw_text, cid, cookie_path):
    results = []
    
    # 1. 115分享
    p115 = r'(https?://(?:115\.com|115cdn\.com)/s/([a-z0-9]+))(?:(?:\?password=|提取码[:：\s]+)([a-z0-9]{4}))?'
    for full_url, code, pwd in re.findall(p115, raw_text, re.IGNORECASE):
        res = lib115.import_115_share(full_url, pwd or "", cid=cid, cookie_path=cookie_path)
        results.append({"type": "115分享", "link": full_url, "status": res['status'], "msg": res['msg']})

    # 2. 磁力/电驴 (离线下载)
    p_offline = r'(magnet:\?xt=urn:btih:[a-z0-9]{32,40}|ed2k://\|file\|[^|]+\|\d+\|[a-z0-9]{32}\|/?)'
    for link in re.findall(p_offline, raw_text, re.IGNORECASE):
        res = lib115.add_task_url(link, cookie_path=cookie_path)
        results.append({"type": "离线任务", "link": link[:40] + "...", "status": res['status'], "msg": res['msg']})

    # 3. 阿里云盘 (尝试离线)
    p_ali = r'(https?://(?:www\.)?(?:alipan\.com|aliyundrive\.com)/s/([a-z0-9]+))'
    for full_url, share_id in re.findall(p_ali, raw_text, re.IGNORECASE):
        res = lib115.add_task_url(full_url, cookie_path=cookie_path)
        results.append({"type": "阿里云盘", "link": full_url, "status": res['status'], "msg": f"提交离线: {res['msg']}"})

    # 4. 秒传 (upload_sha1)
    p_sha1 = r'([^|\n\r]+)\|(\d+)\|([a-fA-F0-9]{40})'
    for name, size, sha1 in re.findall(p_sha1, raw_text):
        if hasattr(lib115, 'upload_sha1'):
            res = lib115.upload_sha1(name, size, sha1, cid=cid, cookie_path=cookie_path)
            results.append({"type": "秒传", "link": name, "status": res['status'], "msg": res['msg']})
            
    return results