#!/usr/bin/env python3
"""
资产数据导出工具
用法:
    python export_assets.py                    # 导出全部资产到 Excel
    python export_assets.py --csv              # 导出 CSV 格式
    python export_assets.py --output /path/to/output.xlsx
    python export_assets.py --keyword "登录"   # 按关键词筛选
    python export_assets.py --platform hunter  # 按平台筛选
    python export_assets.py --limit 1000       # 限制条数
"""
import argparse
import os
import sqlite3
import openpyxl
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'assets.db')


def get_assets(keyword=None, platform=None, limit=None):
    """从数据库读取资产"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    sql = 'SELECT * FROM assets WHERE 1=1'
    params = []
    
    if keyword:
        sql += ' AND (ip LIKE ? OR domain LIKE ? OR web_title LIKE ? OR company LIKE ?)'
        p = f'%{keyword}%'
        params.extend([p, p, p, p])
    
    if platform:
        sql += ' AND platform = ?'
        params.append(platform)
    
    sql += ' ORDER BY found_date DESC'
    
    if limit:
        sql += f' LIMIT {int(limit)}'
    
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def export_to_excel(rows, output_path):
    """导出到 Excel"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "资产列表"
    
    headers = ['ID', 'IP', '端口', '域名', '标题', '协议', 'URL', '省份', '城市', '单位', '平台', '发现时间', '最后可见', '来源关键词', '来源页码']
    ws.append(headers)
    
    for r in rows:
        ws.append([
            r['id'], r['ip'], r['port'], r['domain'], r['web_title'],
            r['protocol'], r['url'], r['province'], r['city'], r['company'],
            r['platform'], r['found_date'], r['last_seen'],
            r['source_keyword'], r['source_page']
        ])
    
    col_widths = [6, 15, 8, 25, 40, 10, 50, 10, 12, 20, 10, 20, 20, 20, 10]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    
    wb.save(output_path)
    print(f"✅ Excel 导出成功: {output_path} ({len(rows)} 条)")


def export_to_csv(rows, output_path):
    """导出到 CSV"""
    import csv
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        if not rows:
            print(f"⚠️  无数据，未生成文件")
            return
        
        writer = csv.writer(f)
        writer.writerow(rows[0].keys())
        for r in rows:
            writer.writerow(r.values())
    
    print(f"✅ CSV 导出成功: {output_path} ({len(rows)} 条)")


def main():
    parser = argparse.ArgumentParser(description='资产数据导出工具')
    parser.add_argument('--csv', action='store_true', help='导出 CSV 格式（默认 Excel）')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径')
    parser.add_argument('--keyword', type=str, default=None, help='按关键词筛选')
    parser.add_argument('--platform', type=str, default=None, help='按平台筛选 (hunter/github)')
    parser.add_argument('--limit', type=int, default=None, help='限制导出条数')
    args = parser.parse_args()
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库不存在: {DB_PATH}")
        return
    
    print(f"📖 读取数据库: {DB_PATH}")
    rows = get_assets(keyword=args.keyword, platform=args.platform, limit=args.limit)
    print(f"📊 共 {len(rows)} 条资产")
    
    if not rows:
        print("⚠️  无数据")
        return
    
    # 生成默认文件名
    if not args.output:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        suffix = 'csv' if args.csv else 'xlsx'
        args.output = os.path.join(os.path.dirname(__file__), f'assets_export_{ts}.{suffix}')
    
    if args.csv:
        export_to_csv(rows, args.output)
    else:
        export_to_excel(rows, args.output)


if __name__ == '__main__':
    main()
