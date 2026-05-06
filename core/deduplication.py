#!/usr/bin/env python3
"""
去重判断逻辑
- IP + 端口 相同 = 重复
- 无IP+端口时，看域名
"""

import sqlite3
from typing import List, Dict, Any, Optional


class Deduplicator:
    """去重器"""
    
    def __init__(self, db_path: str = "database/assets.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
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
                status TEXT DEFAULT '未检测',
                matched_fields TEXT DEFAULT '',
                UNIQUE(ip, port, domain)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerted (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT,
                port INTEGER,
                alert_date TEXT,
                platform TEXT,
                source_keyword TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_key(self, asset: Dict[str, Any]) -> tuple:
        """获取去重 key"""
        ip = asset.get('ip', '')
        port = asset.get('port', 0)
        domain = asset.get('domain', '')
        return (ip, port, domain)
    
    def is_new(self, asset: Dict[str, Any], platform: str = "hunter") -> bool:
        """判断是否是新资产"""
        ip, port, domain = self._get_key(asset)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id FROM assets WHERE ip=? AND port=? AND domain=?',
            (ip, port, domain)
        )
        exists = cursor.fetchone() is not None
        
        conn.close()
        return not exists
    
    def infer_matched_fields(self, asset: Dict[str, Any], source_keyword: str) -> str:
        """
        推断资产通过哪些字段命中
        source_keyword 格式: title="关键词" || web.body="关键词" || cert="关键词" || ...
        返回: 逗号分隔的字段名，如 "title,web.body"
        """
        import re
        # 解析出原始关键词
        keywords_raw = re.findall(r'=\s*["\']?([^"\'\s]+)["\']?', source_keyword)
        if not keywords_raw:
            return ''

        # 原始关键词（整词匹配）
        keyword = keywords_raw[0]
        matched = []

        def contains_any(text, kw):
            """判断 text 是否包含关键词（支持模糊匹配：关键词中任意2字词组在text中）"""
            if not text or not kw:
                return False
            # 精确子串匹配
            if kw in text:
                return True
            # 拆分关键词为2字词组，任意一个在text中即命中（处理Hunter模糊匹配）
            if len(kw) >= 2:
                for i in range(len(kw) - 1):
                    bigram = kw[i:i+2]
                    if bigram in text:
                        return True
            return False

        # web_title → title
        if contains_any(asset.get('web_title', ''), keyword):
            matched.append('title')

        # url
        if contains_any(asset.get('url', ''), keyword):
            matched.append('url')

        # domain
        if contains_any(asset.get('domain', ''), keyword):
            matched.append('domain')

        return ','.join(matched)

    def save_asset(self, asset: Dict[str, Any], platform: str, source_keyword: str, source_page: int = None):
        """保存资产到数据库"""
        ip = asset.get('ip', '')
        port = asset.get('port', 0)
        domain = asset.get('domain', '')
        web_title = asset.get('web_title', '')
        protocol = asset.get('protocol', '')
        url = asset.get('url', '')
        province = asset.get('province', '')
        city = asset.get('city', '')
        company = asset.get('company', '') or ''

        # 推断命中条件
        matched_fields = self.infer_matched_fields(asset, source_keyword)

        import datetime
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO assets
            (ip, port, domain, web_title, protocol, url, province, city, company, platform, found_date, last_seen, source_keyword, source_page, status, matched_fields)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ip, port, domain, web_title, protocol, url, province, city, company, platform, now, now, source_keyword, source_page, '未检测', matched_fields))

        conn.commit()
        conn.close()
    
    def filter_new(self, assets: List[Dict[str, Any]], platform: str, source_keyword: str, source_page: int = None) -> List[Dict[str, Any]]:
        """
        过滤出新增资产
        同时保存新资产到数据库
        """
        new_assets = []
        existing_count = 0
        
        for asset in assets:
            if self.is_new(asset, platform):
                new_assets.append(asset)
                self.save_asset(asset, platform, source_keyword, source_page)
            else:
                existing_count += 1
        
        print(f"[Deduplicator] 本次返回 {len(assets)} 条 | 新增 {len(new_assets)} 条 | 重复 {existing_count} 条")
        return new_assets
    
    def mark_alerted(self, assets: List[Dict[str, Any]], platform: str, source_keyword: str):
        """标记为已告警"""
        import datetime
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for asset in assets:
            ip, port = self._get_key(asset)
            cursor.execute('''
                INSERT INTO alerted (ip, port, alert_date, platform, source_keyword)
                VALUES (?, ?, ?, ?, ?)
            ''', (ip, port, now, platform, source_keyword))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM assets')
        total_assets = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM alerted')
        total_alerted = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_assets': total_assets,
            'total_alerted': total_alerted
        }