import os
import json
import time
import random
import threading # 引入线程锁
import lib_alist
import page_strm_config
import lib_log
from urllib.parse import quote

# === 全局任务锁 (关键部分) ===
_TASK_LOCK = threading.Lock()
_CURRENT_TASK_NAME = None

def is_task_running():
    """检查是否有任务正在运行"""
    return _TASK_LOCK.locked()

def get_running_task_name():
    """获取当前运行的任务名称"""
    return _CURRENT_TASK_NAME

# 视频扩展名过滤器
VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.iso', '.wmv', '.flv', '.ts', '.rmvb', '.m2ts'}

def get_alist_tree_recursive(path):
    """递归获取 AList 目录树 (含防风控延迟)"""
    
    # 目录扫描延迟
    delay = random.uniform(2, 5)
    lib_log.write_log(f"正在扫描目录: {path} (等待 {delay:.1f}s)", "DEBUG")
    time.sleep(delay)

    tree = {}
    res = lib_alist.fs_list(path, page=1, per_page=0)
    
    if not res or not isinstance(res, dict) or not res.get('success'):
        msg = res.get('msg') if res and isinstance(res, dict) else "API无响应"
        lib_log.write_log(f"读取目录失败 {path}: {msg}", "ERROR")
        return tree

    data = res.get('data')
    if not data: return tree

    items = data.get('content') or [] 
    for item in items:
        if not item: continue
        name = item.get('name')
        if not name: continue

        full_path = os.path.join(path, name).replace("\\", "/")
        
        if item.get('is_dir'):
            sub_tree = get_alist_tree_recursive(full_path)
            tree.update(sub_tree)
        else:
            ext = os.path.splitext(name)[1].lower()
            if ext in VIDEO_EXTS:
                tree[full_path] = {'size': item.get('size'), 'name': name}
    return tree

def generate_strm_content(prefix, mount_path, file_full_path):
    encoded_path = quote(file_full_path)
    base = prefix.rstrip('/')
    return f"{base}/d{encoded_path}"

def sync_quark_incremental_stateless(src_root, local_dst):
    """【后台线程版】增量同步"""
    global _CURRENT_TASK_NAME
    stats = {"scanned": 0, "added": 0, "skipped": 0, "errors": 0}
    
    # --- 1. 尝试获取锁 ---
    if not _TASK_LOCK.acquire(blocking=False):
        msg = f"任务拒绝：系统正如火如荼地执行 [{_CURRENT_TASK_NAME}]，请稍后再试。"
        lib_log.write_log(msg, "WARNING")
        return stats
    
    _CURRENT_TASK_NAME = "增量同步"
    
    try:
        strm_cfg = page_strm_config.load_strm_config()
        prefix = strm_cfg.get('url_prefix')
        if not prefix:
            lib_log.write_log("❌ 任务终止：未配置 STRM 播放前缀", "ERROR")
            return stats

        lib_log.write_log(f"🚀 [增量任务启动] 源: {src_root}")
        
        cloud_files = get_alist_tree_recursive(src_root)
        stats['scanned'] = len(cloud_files)
        lib_log.write_log(f"📊 扫描完成，共 {len(cloud_files)} 个视频，开始比对...")

        for fpath, meta in cloud_files.items():
            try:
                rel_path = os.path.relpath(fpath, src_root)
                local_dir = os.path.join(local_dst, os.path.dirname(rel_path))
                strm_name = os.path.splitext(meta['name'])[0] + ".strm"
                local_strm_path = os.path.join(local_dir, strm_name)
                
                if os.path.exists(local_strm_path):
                    stats['skipped'] += 1
                    continue
                    
                if not os.path.exists(local_dir):
                    os.makedirs(local_dir)
                
                content = generate_strm_content(prefix, src_root, fpath)
                
                with open(local_strm_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                stats['added'] += 1
                lib_log.write_log(f"✅ 生成: {strm_name}", "INFO")

                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                stats['errors'] += 1
                lib_log.write_log(f"❌ 失败 {fpath}: {e}", "ERROR")

        lib_log.write_log(f"🏁 [增量任务结束] 新增: {stats['added']}, 跳过: {stats['skipped']}")
        
    except Exception as main_e:
        lib_log.write_log(f"❌ 任务异常: {main_e}", "CRITICAL")
    
    finally:
        # --- 2. 释放锁 ---
        _CURRENT_TASK_NAME = None
        _TASK_LOCK.release()
        
    return stats

def sync_quark_full(src_root, local_dst):
    """【后台线程版】全量同步"""
    global _CURRENT_TASK_NAME
    stats = {"scanned": 0, "created": 0, "errors": 0}
    
    if not _TASK_LOCK.acquire(blocking=False):
        msg = f"任务拒绝：系统正在执行 [{_CURRENT_TASK_NAME}]"
        lib_log.write_log(msg, "WARNING")
        return stats
        
    _CURRENT_TASK_NAME = "全量同步"

    try:
        strm_cfg = page_strm_config.load_strm_config()
        prefix = strm_cfg.get('url_prefix')
        if not prefix:
            lib_log.write_log("❌ 任务终止：未配置 STRM 播放前缀", "ERROR")
            return stats

        lib_log.write_log(f"🔥 [全量任务启动] 强制覆盖模式", "WARNING")
        
        cloud_files = get_alist_tree_recursive(src_root)
        stats['scanned'] = len(cloud_files)
        lib_log.write_log(f"📊 扫描完成，准备覆盖 {len(cloud_files)} 个文件...")

        for fpath, meta in cloud_files.items():
            try:
                rel_path = os.path.relpath(fpath, src_root)
                local_dir = os.path.join(local_dst, os.path.dirname(rel_path))
                strm_name = os.path.splitext(meta['name'])[0] + ".strm"
                local_strm_path = os.path.join(local_dir, strm_name)
                
                if not os.path.exists(local_dir):
                    os.makedirs(local_dir)
                
                content = generate_strm_content(prefix, src_root, fpath)
                
                with open(local_strm_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                stats['created'] += 1
                lib_log.write_log(f"♻️ 覆盖: {strm_name}", "INFO")

                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                stats['errors'] += 1
                lib_log.write_log(f"❌ 失败 {fpath}: {e}", "ERROR")
                
        lib_log.write_log(f"🏁 [全量任务结束] 处理: {stats['created']}")

    except Exception as main_e:
        lib_log.write_log(f"❌ 任务异常: {main_e}", "CRITICAL")
        
    finally:
        _CURRENT_TASK_NAME = None
        _TASK_LOCK.release()
        
    return stats