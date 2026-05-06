#!/usr/bin/env python3
"""
资产查询工具
直接运行: python query_assets.py
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'assets.db')


def get_all_assets(limit=50):
    """查询所有资产"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM assets')
    total = cursor.fetchone()[0]
    print(f"总资产数: {total}\n")
    
    cursor.execute('''
        SELECT ip, port, protocol, web_title, domain, province, city, company, platform, source_keyword, found_date
        FROM assets
        ORDER BY found_date DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("暂无数据")
        return
    
    print(f"{'IP':<16} {'端口':<6} {'协议':<6} {'标题':<25} {'域名':<20} {'地区':<10} {'公司':<15} {'平台':<8} {'时间'}")
    print("-" * 130)
    
    for r in rows:
        ip, port, protocol, web_title, domain, province, city, company, platform, keyword, date = r
        title = (web_title or '-')[:24]
        dom = (domain or '-')[:19]
        loc = f"{province or ''}{city or ''}"[:9]
        comp = (company or '-')[:14]
        date_str = (date or '-')[:10]
        print(f"{ip:<16} {port:<6} {protocol or '-':<6} {title:<25} {dom:<20} {loc:<10} {comp:<15} {platform:<8} {date_str}")


def search(keyword):
    """按关键词搜索"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ip, port, protocol, web_title, domain, province, city, company, platform, found_date
        FROM assets
        WHERE source_keyword LIKE ? OR web_title LIKE ? OR domain LIKE ? OR ip LIKE ?
        ORDER BY found_date DESC
        LIMIT 100
    ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    
    rows = cursor.fetchall()
    conn.close()
    
    print(f"搜索 '{keyword}' 结果: {len(rows)} 条\n")
    
    if not rows:
        return
    
    print(f"{'IP':<16} {'端口':<6} {'协议':<6} {'标题':<25} {'地区':<10} {'公司'}")
    print("-" * 90)
    
    for r in rows:
        ip, port, protocol, web_title, domain, province, city, company, platform, date = r
        title = (web_title or '-')[:24]
        loc = f"{province or ''}{city or ''}"[:9]
        comp = (company or '-')[:20]
        print(f"{ip:<16} {port:<6} {protocol or '-':<6} {title:<25} {loc:<10} {comp}")


def stats():
    """统计"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n=== 统计 ===\n")
    
    cursor.execute('SELECT COUNT(*) FROM assets')
    print(f"总资产: {cursor.fetchone()[0]} 条")
    
    cursor.execute('SELECT platform, COUNT(*) FROM assets GROUP BY platform')
    print("\n按平台:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 条")
    
    cursor.execute('SELECT source_keyword, COUNT(*) FROM assets GROUP BY source_keyword ORDER BY COUNT(*) DESC')
    print("\n按查询词:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 条")
    
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--stats':
            stats()
        else:
            search(sys.argv[1])
    else:
        get_all_assets()
