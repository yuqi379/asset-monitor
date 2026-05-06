#!/usr/bin/env python3
"""
迁移：为 assets 表添加 matched_fields 字段
用于记录每条资产是通过哪些搜索字段命中的
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'assets.db')


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(assets)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'matched_fields' not in columns:
        cursor.execute("ALTER TABLE assets ADD COLUMN matched_fields TEXT DEFAULT ''")
        conn.commit()
        print("[Migration 003] 已添加 matched_fields 字段")
    else:
        print("[Migration 003] matched_fields 字段已存在，跳过")

    conn.close()


if __name__ == "__main__":
    migrate()
