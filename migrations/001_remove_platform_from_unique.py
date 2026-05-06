#!/usr/bin/env python3
"""
迁移脚本模板
使用方法: python migrations/001_remove_platform_from_unique.py

每次表结构变更:
1. 复制本文件为新序号
2. 修改 upgrade() 函数
3. 运行脚本
"""

import sqlite3
import shutil
import os
import sys
from datetime import datetime

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'assets.db')


def backup():
    """备份数据库"""
    if not os.path.exists(DB_PATH):
        print("[SKIP] 数据库不存在，无需备份")
        return

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{DB_PATH}.{ts}"
    shutil.copy(DB_PATH, backup_path)
    print(f"[BACKUP] {backup_path}")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def upgrade():
    """
    执行升级
    将 UNIQUE(ip, port, domain, platform) 改为 UNIQUE(ip, port, domain)
    """
    print("[UPGRADE] 开始迁移...")

    conn = get_connection()

    # 1. 检查当前约束
    indexes = conn.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='index' AND sql IS NOT NULL
    """).fetchall()
    print("[CHECK] 当前索引:")
    for idx in indexes:
        print(f"  - {idx['name']}: {idx['sql']}")

    # 2. 删除旧索引
    conn.execute('DROP INDEX IF EXISTS assets_ip_port_domain_platform')
    conn.execute('DROP INDEX IF EXISTS assets_ip_port_domain_platform_platform')
    print("[DROP] 删除旧索引 assets_ip_port_domain_platform")

    # 3. 创建新唯一索引（不包含 platform）
    conn.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS assets_ip_port_domain
        ON assets(ip, port, domain)
    ''')
    print("[CREATE] 新索引 assets_ip_port_domain(ip, port, domain)")

    conn.commit()
    conn.close()
    print("[DONE] 迁移完成")


def rollback():
    """回滚（从备份恢复）"""
    backups = [f for f in os.listdir(os.path.dirname(DB_PATH))
               if f.startswith('assets.db.')]
    if not backups:
        print("[ERROR] 未找到备份文件")
        return

    latest = sorted(backups)[-1]
    backup_path = os.path.join(os.path.dirname(DB_PATH), latest)
    shutil.copy(backup_path, DB_PATH)
    print(f"[ROLLBACK] 已恢复至 {latest}")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        rollback()
    else:
        backup()
        upgrade()
