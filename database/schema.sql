-- 资产表
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT,
    port INTEGER,
    domain TEXT,
    web_title TEXT,
    protocol TEXT,
    url TEXT,
    province TEXT,
    city TEXT,
    company TEXT,
    platform TEXT,
    found_date TEXT,
    last_seen TEXT,
    source_keyword TEXT,
    source_page INTEGER,
    UNIQUE(ip, port, domain)
);

-- 已推送记录（去重）
CREATE TABLE IF NOT EXISTS alerted (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT,
    port INTEGER,
    alert_date TEXT,
    platform TEXT,
    source_keyword TEXT
);

-- 项目配置表
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    query_keyword TEXT,
    pages_per_account INTEGER DEFAULT 5,
    enabled INTEGER DEFAULT 1,
    last_run TEXT
);

-- Hunter账号状态表
CREATE TABLE IF NOT EXISTS hunter_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key TEXT,
    idx INTEGER,
    start_page INTEGER,
    end_page INTEGER,
    daily_quota INTEGER DEFAULT 500,
    used_today INTEGER DEFAULT 0,
    last_used TEXT,
    enabled INTEGER DEFAULT 1
);