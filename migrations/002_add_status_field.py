#!/usr/bin/env python3
"""
Migration 002: 给 assets 表添加 status 字段
状态值：未检测 / 异常 / 无异常
"""

import sqlite3
import os

def migrate(db_path: str):
    print(f"[Migration 002] 迁移数据库: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(assets)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'status' in columns:
        print("[Migration 002] status 字段已存在，跳过")
        conn.close()
        return

    # 添加 status 字段
    cursor.execute("ALTER TABLE assets ADD COLUMN status TEXT DEFAULT '未检测'")
    conn.commit()
    print("[Migration 002] 已添加 status 字段，默认值: 未检测")

    # 验证
    cursor.execute("PRAGMA table_info(assets)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"[Migration 002] 当前表字段: {columns}")

    conn.close()
    print("[Migration 002] 迁移完成")


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'assets.db')
    migrate(db_path)
