import sqlite3
import os

DB_FILE = "config.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. 配置表
    c.execute('''CREATE TABLE IF NOT EXISTS config_115 (id INTEGER PRIMARY KEY CHECK (id = 1), cookie_path TEXT, device_type TEXT, api_interval REAL, default_cid TEXT DEFAULT '0')''')
    try:
        c.execute("PRAGMA table_info(config_115)")
        if 'default_cid' not in [i[1] for i in c.fetchall()]: c.execute("ALTER TABLE config_115 ADD COLUMN default_cid TEXT DEFAULT '0'")
    except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS config_aliyun (id INTEGER PRIMARY KEY CHECK (id = 1), refresh_token TEXT, access_token TEXT, expire_time INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config_quark (id INTEGER PRIMARY KEY CHECK (id = 1), cookie TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config_scheduler (id INTEGER PRIMARY KEY CHECK (id = 1), cron_expression TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config_tmdb (id INTEGER PRIMARY KEY CHECK (id = 1), api_domain TEXT, image_domain TEXT, api_key TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config_proxy (id INTEGER PRIMARY KEY CHECK (id = 1), http_proxy TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config_pansearch (id INTEGER PRIMARY KEY CHECK (id = 1), api_url TEXT, api_token TEXT)''')

    # 2. 业务数据表
    c.execute('''CREATE TABLE IF NOT EXISTS movies (tmdb_id INTEGER PRIMARY KEY, title TEXT, original_title TEXT, overview TEXT, poster_path TEXT, release_date TEXT, vote_average REAL, popularity REAL, genre_ids TEXT, update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tv_shows (tmdb_id INTEGER PRIMARY KEY, name TEXT, original_name TEXT, overview TEXT, poster_path TEXT, first_air_date TEXT, vote_average REAL, popularity REAL, genre_ids TEXT, update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (tmdb_id INTEGER, media_type TEXT, name TEXT, poster_path TEXT, subscribe_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (tmdb_id, media_type))''')
    
    # 3. 转存记录表 (Log)
    c.execute('''CREATE TABLE IF NOT EXISTS transfer_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_type TEXT, 
        title TEXT, 
        link TEXT, 
        status INTEGER, 
        message TEXT, 
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit(); conn.close()

# --- 配置存取 ---
def save_115_config(p, d, i, c): conn = sqlite3.connect(DB_FILE); conn.execute('INSERT OR REPLACE INTO config_115 VALUES (1, ?, ?, ?, ?)', (p, d, i, c)); conn.commit(); conn.close()
def load_115_config(): conn = sqlite3.connect(DB_FILE); c = conn.cursor(); c.execute('SELECT * FROM config_115 WHERE id=1'); r = c.fetchone(); conn.close(); return {"cookie_path": r[1], "device_type": r[2], "api_interval": r[3], "default_cid": r[4]} if r else {"cookie_path": "config/115-cookies.txt", "device_type": "Web", "api_interval": 3.0, "default_cid": "0"}
def save_aliyun_config(rt): conn = sqlite3.connect(DB_FILE); conn.execute('INSERT OR REPLACE INTO config_aliyun (id, refresh_token) VALUES (1, ?)', (rt,)); conn.commit(); conn.close()
def load_aliyun_config(): conn = sqlite3.connect(DB_FILE); c = conn.cursor(); c.execute('SELECT refresh_token FROM config_aliyun WHERE id=1'); r = c.fetchone(); conn.close(); return {"refresh_token": r[0]} if r else {"refresh_token": ""}
def save_quark_config(c_val): conn = sqlite3.connect(DB_FILE); conn.execute('INSERT OR REPLACE INTO config_quark (id, cookie) VALUES (1, ?)', (c_val,)); conn.commit(); conn.close()
def load_quark_config(): conn = sqlite3.connect(DB_FILE); c = conn.cursor(); c.execute('SELECT cookie FROM config_quark WHERE id=1'); r = c.fetchone(); conn.close(); return {"cookie": r[0]} if r else {"cookie": ""}
def save_scheduler_config(cron): conn = sqlite3.connect(DB_FILE); conn.execute('INSERT OR REPLACE INTO config_scheduler VALUES (1, ?)', (cron,)); conn.commit(); conn.close()
def load_scheduler_config(): conn = sqlite3.connect(DB_FILE); c = conn.cursor(); c.execute('SELECT cron_expression FROM config_scheduler WHERE id=1'); r = c.fetchone(); conn.close(); return r[0] if r else "*/20 8-23 * * *"
def save_tmdb_config(a, i, k): conn=sqlite3.connect(DB_FILE); conn.execute('INSERT OR REPLACE INTO config_tmdb VALUES (1, ?, ?, ?)', (a, i, k)); conn.commit(); conn.close()
def load_tmdb_config(): conn=sqlite3.connect(DB_FILE); c=conn.cursor(); c.execute('SELECT * FROM config_tmdb WHERE id=1'); r=c.fetchone(); conn.close(); return {"api_domain":r[1],"image_domain":r[2],"api_key":r[3]} if r else {"api_domain":"https://api.tmdb.org","image_domain":"https://image.tmdb.org","api_key":""}
def save_pansearch_config(u, t): conn=sqlite3.connect(DB_FILE); conn.execute('INSERT OR REPLACE INTO config_pansearch VALUES (1, ?, ?)', (u, t)); conn.commit(); conn.close()
def load_pansearch_config(): conn=sqlite3.connect(DB_FILE); c=conn.cursor(); c.execute('SELECT * FROM config_pansearch WHERE id=1'); r=c.fetchone(); conn.close(); return {"api_url":r[1],"api_token":r[2]} if r else {"api_url":"http://192.168.68.200:8080","api_token":""}
def save_proxy_config(p): conn=sqlite3.connect(DB_FILE); conn.execute('INSERT OR REPLACE INTO config_proxy VALUES (1, ?)', (p,)); conn.commit(); conn.close()
def load_proxy_config(): conn=sqlite3.connect(DB_FILE); c=conn.cursor(); c.execute('SELECT * FROM config_proxy WHERE id=1'); r=c.fetchone(); conn.close(); return {"http_proxy":r[1]} if r else {"http_proxy":""}

# --- 业务数据 ---
def save_movies(l): conn=sqlite3.connect(DB_FILE); c=conn.cursor(); [c.execute('INSERT OR REPLACE INTO movies (tmdb_id, title, original_title, overview, poster_path, release_date, vote_average, popularity, genre_ids) VALUES (?,?,?,?,?,?,?,?,?)', (m['id'], m['title'], m['original_title'], m['overview'], m['poster_path'], m.get('release_date',''), m.get('vote_average',0), m.get('popularity',0), str(m.get('genre_ids',[])))) for m in l]; conn.commit(); conn.close()
def get_movies(limit=24, offset=0, keyword=None): 
    conn=sqlite3.connect(DB_FILE); c=conn.cursor(); q="SELECT * FROM movies"; p=[]
    if keyword: q+=" WHERE title LIKE ?"; p.append(f"%{keyword}%")
    q+=" ORDER BY popularity DESC LIMIT ? OFFSET ?"; p.extend([limit, offset]); c.execute(q, p); rows=c.fetchall(); conn.close()
    return [{"id":r[0], "title":r[1], "poster_path":r[4], "release_date":r[5], "vote_average":r[6], "popularity":r[7]} for r in rows]
def get_movie_count(keyword=None): conn=sqlite3.connect(DB_FILE); c=conn.cursor(); q="SELECT count(*) FROM movies"; p=[]; q+=" WHERE title LIKE ?" if keyword else ""; p.append(f"%{keyword}%") if keyword else None; c.execute(q, p); n=c.fetchone()[0]; conn.close(); return n
def save_tv_shows(l): conn=sqlite3.connect(DB_FILE); c=conn.cursor(); [c.execute('INSERT OR REPLACE INTO tv_shows (tmdb_id, name, original_name, overview, poster_path, first_air_date, vote_average, popularity, genre_ids) VALUES (?,?,?,?,?,?,?,?,?)', (t['id'], t['name'], t['original_name'], t['overview'], t['poster_path'], t.get('first_air_date', ''), t.get('vote_average', 0), t.get('popularity', 0), str(t.get('genre_ids', [])))) for t in l]; conn.commit(); conn.close()
def get_tv_shows(limit=24, offset=0, keyword=None): conn=sqlite3.connect(DB_FILE); c=conn.cursor(); q="SELECT * FROM tv_shows"; p=[]; q+=" WHERE name LIKE ?" if keyword else ""; p.append(f"%{keyword}%") if keyword else None; q+=" ORDER BY popularity DESC LIMIT ? OFFSET ?"; p.extend([limit, offset]); c.execute(q, p); rows=c.fetchall(); conn.close(); return [{"id":r[0], "name":r[1], "poster_path":r[4], "first_air_date":r[5], "vote_average":r[6], "popularity":r[7]} for r in rows]
def get_tv_count(keyword=None): conn=sqlite3.connect(DB_FILE); c=conn.cursor(); q="SELECT count(*) FROM tv_shows"; p=[]; q+=" WHERE name LIKE ?" if keyword else ""; p.append(f"%{keyword}%") if keyword else None; c.execute(q, p); n=c.fetchone()[0]; conn.close(); return n
def add_subscription(tmdb_id, media_type, name, poster_path): conn = sqlite3.connect(DB_FILE); conn.execute('INSERT OR IGNORE INTO subscriptions (tmdb_id, media_type, name, poster_path) VALUES (?, ?, ?, ?)', (tmdb_id, media_type, name, poster_path)); conn.commit(); conn.close()
def remove_subscription(tmdb_id, media_type): conn = sqlite3.connect(DB_FILE); conn.execute('DELETE FROM subscriptions WHERE tmdb_id = ? AND media_type = ?', (tmdb_id, media_type)); conn.commit(); conn.close()
def get_subscriptions(): conn = sqlite3.connect(DB_FILE); c = conn.cursor(); c.execute('SELECT * FROM subscriptions ORDER BY subscribe_time DESC'); rows = c.fetchall(); conn.close(); return [{"id": r[0], "type": r[1], "name": r[2], "poster_path": r[3]} for r in rows]
def check_is_subscribed(tmdb_id, media_type): conn = sqlite3.connect(DB_FILE); c = conn.cursor(); c.execute('SELECT count(*) FROM subscriptions WHERE tmdb_id = ? AND media_type = ?', (tmdb_id, media_type)); exists = c.fetchone()[0] > 0; conn.close(); return exists

# --- 日志记录 ---
def add_transfer_log(log_type, title, link, status, message):
    conn = sqlite3.connect(DB_FILE); st_int = 1 if status else 0
    conn.execute('INSERT INTO transfer_history (log_type, title, link, status, message) VALUES (?, ?, ?, ?, ?)', (log_type, title, link, st_int, str(message)))
    conn.commit(); conn.close()

def get_transfer_logs(limit=50, offset=0, status_filter=None):
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    sql = "SELECT id, log_type, title, link, status, message, create_time FROM transfer_history"
    params = []
    if status_filter is not None: sql += " WHERE status = ?"; params.append(status_filter)
    sql += " ORDER BY create_time DESC LIMIT ? OFFSET ?"; params.extend([limit, offset])
    c.execute(sql, params); rows = c.fetchall(); conn.close()
    return [{"id": r[0], "type": r[1], "title": r[2], "link": r[3], "status": bool(r[4]), "msg": r[5], "time": r[6]} for r in rows]

def clear_transfer_logs():
    conn = sqlite3.connect(DB_FILE); conn.execute('DELETE FROM transfer_history'); conn.commit(); conn.close()

init_db()