import sqlite3
import datetime
import os
import random

DB_FILE = "system_logs.db"

def _get_conn():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    # 确保表存在
    conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            level TEXT,
            message TEXT
        )
    ''')
    return conn

def write_log(message, level="INFO"):
    """
    写入日志到数据库
    :param message: 日志内容
    :param level: INFO, ERROR, WARNING, CRITICAL, DEBUG
    """
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        
        # 插入日志
        # 注意：sqlite 的 CURRENT_TIMESTAMP 是 UTC 时间，我们手动写入本地时间更直观
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)", 
                       (now_str, level, message))
        
        # 10% 的概率触发自动清理 (删除超过7天的日志)
        if random.random() < 0.1:
            seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("DELETE FROM logs WHERE timestamp < ?", (seven_days_ago,))
            
        conn.commit()
        conn.close()
        
        # 同时打印到控制台，方便 docker logs 查看
        print(f"[{now_str}] [{level}] {message}")
        
    except Exception as e:
        print(f"日志数据库写入失败: {e}")

def read_logs_db(limit=100, offset=0, level_filter=None):
    """
    从数据库读取日志 (分页 + 筛选)
    """
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        
        query = "SELECT id, timestamp, level, message FROM logs"
        params = []
        
        if level_filter and level_filter != "ALL":
            query += " WHERE level = ?"
            params.append(level_filter)
            
        # 按时间倒序
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    except Exception as e:
        return []

def get_total_logs_count(level_filter=None):
    """获取日志总数"""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM logs"
        params = []
        if level_filter and level_filter != "ALL":
            query += " WHERE level = ?"
            params.append(level_filter)
            
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def clear_logs():
    """清空所有日志"""
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM logs")
        conn.commit()
        conn.close()
        return True
    except:
        return False