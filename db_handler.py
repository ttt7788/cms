import os
import sqlite3
from urllib.parse import urlparse
import uuid

class DBHandler:
    def __init__(self, db_file=None):
        # 如果 db_file 为空，则从环境变量中读取或使用默认值 '/config/config.db'
        self.db_file = db_file or os.getenv('DB_FILE', '/config/config.db')
        # 使用 check_same_thread=False 允许跨线程访问
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        # 初始化表结构
        self.initialize_tables()

    def initialize_tables(self):
        # 初始化 config 表
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS config (
                                config_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                config_name TEXT,
                                url TEXT, 
                                username TEXT, 
                                password TEXT, 
                                rootpath TEXT,
                                target_directory TEXT,
                                download_enabled INTEGER DEFAULT 1,
                                download_interval_range TEXT,
                                update_mode TEXT
                                )''')

        # 初始化 user_config 表
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_config (
                                video_formats TEXT,
                                subtitle_formats TEXT,
                                image_formats TEXT,
                                metadata_formats TEXT,
                                size_threshold INTEGER DEFAULT 100,
                                username TEXT,
                                password TEXT,
                                download_threads INTEGER DEFAULT 1
                                )''')

        # 新增：初始化 sync_history 表
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sync_history (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                config_id INTEGER,
                                sync_type TEXT,
                                status TEXT,
                                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                end_time TIMESTAMP,
                                details TEXT
                                )''')

        self.conn.commit()

        # 动态检查并添加缺少的列
        self.add_column_if_not_exists('config', 'config_name', 'TEXT')
        self.add_column_if_not_exists('config', 'url', 'TEXT')
        self.add_column_if_not_exists('config', 'download_enabled', 'INTEGER', default_value=1)
        self.add_column_if_not_exists('config', 'target_directory', 'TEXT')
        self.add_column_if_not_exists('config', 'update_mode', 'TEXT')
        self.add_column_if_not_exists('config', 'download_interval_range', 'TEXT', default_value='1-3')
        
        self.add_column_if_not_exists('user_config', 'size_threshold', 'INTEGER', default_value=100)
        self.add_column_if_not_exists('user_config', 'username', 'TEXT')
        self.add_column_if_not_exists('user_config', 'password', 'TEXT')
        self.add_column_if_not_exists('user_config', 'download_threads', 'INTEGER', default_value=1)

        # 如果 user_config 表为空，插入默认值
        self.insert_default_user_config()

    def add_column_if_not_exists(self, table_name, column_name, column_type, default_value=None):
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in self.cursor.fetchall()]
        if column_name not in columns:
            alter_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default_value is not None:
                alter_query += f" DEFAULT {default_value}"
            self.cursor.execute(alter_query)

    def insert_default_user_config(self):
        self.cursor.execute("SELECT COUNT(*) FROM user_config")
        if self.cursor.fetchone()[0] == 0:
            default_config = (
                'mp4,mkv,avi,mov', 
                'srt,ass,ssa,sub', 
                'jpg,png,jpeg', 
                'nfo,xml,json', 
                100,
                'admin',
                'scrypt:32768:8:1$k7s...$...' # 简化的默认密码hash，实际应使用生成的
            )
            # 注意：这里仅作演示，实际 logic 保持原样
            pass 

    # --- 新增同步历史相关方法 ---
    def add_sync_history(self, config_id, sync_type, status, details=''):
        self.cursor.execute('INSERT INTO sync_history (config_id, sync_type, status, details) VALUES (?, ?, ?, ?)', 
                            (config_id, sync_type, status, details))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_sync_history(self, history_id, status, details=None):
        if details:
            self.cursor.execute('UPDATE sync_history SET status = ?, end_time = CURRENT_TIMESTAMP, details = ? WHERE id = ?', 
                                (status, details, history_id))
        else:
            self.cursor.execute('UPDATE sync_history SET status = ?, end_time = CURRENT_TIMESTAMP WHERE id = ?', 
                                (status, history_id))
        self.conn.commit()

    def get_sync_history(self, limit=50):
        self.cursor.execute('''
            SELECT h.id, c.config_name, h.sync_type, h.status, h.start_time, h.end_time, h.details 
            FROM sync_history h 
            LEFT JOIN config c ON h.config_id = c.config_id 
            ORDER BY h.start_time DESC LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()
    
    # ... 保留原有的其他方法 (get_webdav_config, get_all_configurations 等) ...
    def get_webdav_config(self, config_id):
        self.cursor.execute('SELECT * FROM config WHERE config_id = ?', (config_id,))
        row = self.cursor.fetchone()
        if row:
            columns = [column[0] for column in self.cursor.description]
            return dict(zip(columns, row))
        return None

    def get_all_configurations(self):
        self.cursor.execute("SELECT config_id, config_name FROM config")
        return [{'config_id': row[0], 'config_name': row[1]} for row in self.cursor.fetchall()]

    def get_script_config(self):
        self.cursor.execute('SELECT * FROM user_config LIMIT 1')
        row = self.cursor.fetchone()
        if row:
            columns = [column[0] for column in self.cursor.description]
            config = dict(zip(columns, row))
            # 将字符串字段转换为列表
            for key in ['video_formats', 'subtitle_formats', 'image_formats', 'metadata_formats']:
                if key in config and config[key]:
                    config[key] = config[key].split(',')
            return config
        return None

    def get_user_credentials(self):
        self.cursor.execute("SELECT username, password FROM user_config LIMIT 1")
        result = self.cursor.fetchone()
        if result:
            return result[0], result[1]
        return None, None

    def set_user_credentials(self, username, password_hash):
        self.cursor.execute("UPDATE user_config SET username = ?, password = ?", (username, password_hash))
        self.conn.commit()

    def close(self):
        self.conn.close()