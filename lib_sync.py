import os
import lib_115_drive
import time
from urllib.parse import quote

# 支持的视频后缀
VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.iso', '.wmv', '.flv', '.ts', '.rmvb', '.m2ts'}

def generate_strm_url(alist_host, mount_path, rel_path, file_name):
    """
    生成指向 AList 的播放链接
    :param alist_host: http://192.168.1.5:5244
    :param mount_path: /115
    :param rel_path: 电影/动作片
    :param file_name: 速度与激情.mp4
    """
    # 拼接路径: /115/电影/动作片/速度与激情.mp4
    full_path = os.path.join(mount_path, rel_path, file_name).replace("\\", "/")
    # URL 编码 (解决中文和特殊字符问题)
    encoded_path = quote(full_path)
    # AList 的直链地址通常是 /d/路径
    return f"{alist_host.rstrip('/')}/d{encoded_path}"

def sync_115_to_strm(src_cid, local_root, alist_host, alist_mount, callback=None):
    """
    执行同步主逻辑
    :param callback: 用于向前端发送日志的函数 func(msg)
    """
    stats = {"dirs": 0, "files": 0, "skips": 0, "errors": 0}
    
    # 任务队列: (当前CID, 当前相对路径)
    queue = [(src_cid, "")]
    
    while queue:
        curr_cid, curr_rel = queue.pop(0)
        
        # 1. 获取 115 文件列表
        res = lib_115_drive.get_files(curr_cid)
        if not res['success']:
            if callback: callback(f"❌ 读取目录失败 [CID:{curr_cid}]: {res['msg']}")
            stats['errors'] += 1
            continue
            
        stats['dirs'] += 1
        
        # 2. 确保本地目录存在
        local_dir = os.path.join(local_root, curr_rel)
        if not os.path.exists(local_dir):
            try:
                os.makedirs(local_dir)
            except Exception as e:
                if callback: callback(f"❌ 创建目录失败: {local_dir}")
                stats['errors'] += 1
                continue

        # 3. 处理文件项
        for item in res['data']:
            name = item.get('n')
            
            # --- 处理子文件夹 ---
            if 'fid' not in item: 
                new_rel = os.path.join(curr_rel, name)
                queue.append((item.get('cid'), new_rel))
                continue
                
            # --- 处理文件 ---
            ext = os.path.splitext(name)[1].lower()
            if ext in VIDEO_EXTS:
                try:
                    # STRM 文件名
                    strm_name = os.path.splitext(name)[0] + ".strm"
                    strm_path = os.path.join(local_dir, strm_name)
                    
                    # 生成目标 URL
                    target_url = generate_strm_url(alist_host, alist_mount, curr_rel, name)
                    
                    # 检查是否需要写入 (跳过已存在且内容一致的文件)
                    if os.path.exists(strm_path):
                        with open(strm_path, 'r', encoding='utf-8') as f:
                            if f.read().strip() == target_url:
                                stats['skips'] += 1
                                continue
                    
                    # 写入 STRM
                    with open(strm_path, 'w', encoding='utf-8') as f:
                        f.write(target_url)
                    
                    stats['files'] += 1
                    if callback: callback(f"✅ 生成: {strm_name}")
                    
                except Exception as e:
                    stats['errors'] += 1
                    if callback: callback(f"❌ 写入文件失败 {name}: {e}")

    return stats