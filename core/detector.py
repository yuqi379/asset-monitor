#!/usr/bin/env python3
"""
资产检测模块
- 读取未检测的资产
- 访问页面，获取HTML源码
- 用原始关键词（source_keyword）匹配HTML内容
- 更新资产状态：异常 / 无异常
"""

import os
import ssl
import urllib.request
import urllib.error
import sqlite3
import time
import re
from typing import List, Dict, Any, Optional, Tuple


# 禁用SSL验证（避免证书问题）
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


class Detector:
    """页面内容检测器"""

    def __init__(self, db_path: str, delay: float = 2.0, timeout: int = 10):
        self.db_path = db_path
        self.delay = delay
        self.timeout = timeout

    def get_unchecked_assets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取待检测的资产"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, ip, port, domain, url, web_title, source_keyword, status
            FROM assets
            WHERE status = '未检测'
            ORDER BY id
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'id': r[0],
                'ip': r[1],
                'port': r[2],
                'domain': r[3],
                'url': r[4],
                'web_title': r[5],
                'source_keyword': r[6],
                'status': r[7],
            }
            for r in rows
        ]

    def build_target_url(self, asset: Dict[str, Any]) -> str:
        """
        构建目标URL
        优先用domain，否则用 ip:port
        """
        domain = asset.get('domain')
        ip = asset.get('ip')
        port = asset.get('port')
        url = asset.get('url')

        # 如果有完整URL，直接用
        if url and url.startswith('http'):
            return url

        # 优先domain
        if domain:
            return f"http://{domain}"

        # 否则用 ip:port
        return f"http://{ip}:{port}"

    def fetch_html(self, url: str) -> Tuple[bool, str]:
        """
        获取页面HTML源码
        返回: (是否成功, html内容或错误信息)
        """
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,*/*',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                }
            )

            with urllib.request.urlopen(req, timeout=self.timeout, context=SSL_CTX) as response:
                html = response.read().decode('utf-8', errors='replace')
                return True, html

        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            return False, f"URL Error: {e.reason}"
        except Exception as e:
            return False, str(e)

    def keyword_match(self, html: str, keyword: str) -> bool:
        """
        检测HTML中是否包含关键词
        使用正则匹配，忽略大小写
        """
        if not keyword or not html:
            return False

        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.search(html) is not None

    def detect_asset(self, asset: Dict[str, Any]) -> Tuple[str, str]:
        """
        检测单条资产
        返回: (状态, 备注)
        """
        keyword = asset.get('source_keyword', '')
        target_url = self.build_target_url(asset)

        print(f"  [检测] {asset['id']} - {target_url} (关键词: {keyword})")

        # 获取HTML
        success, html_or_error = self.fetch_html(target_url)

        if not success:
            # 无法访问，暂不标记，留到下次重试
            return '未检测', f"访问失败: {html_or_error}"

        # 关键词匹配
        matched = self.keyword_match(html_or_error, keyword)

        if matched:
            return '异常', f"命中关键词: {keyword}"
        else:
            return '无异常', ''

    def detect_batch(self, limit: int = 100) -> Dict[str, int]:
        """
        批量检测
        返回: {'total': N, '异常': N, '无异常': N, '失败': N}
        """
        assets = self.get_unchecked_assets(limit)

        if not assets:
            print("[Detector] 没有待检测的资产")
            return {'total': 0, '异常': 0, '无异常': 0, '失败': 0}

        print(f"[Detector] 开始检测 {len(assets)} 条资产...")

        results = {'异常': 0, '无异常': 0, '失败': 0}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for asset in assets:
            status, note = self.detect_asset(asset)

            if status == '未检测':
                results['失败'] += 1
                continue

            # 更新数据库
            cursor.execute(
                'UPDATE assets SET status = ?, last_seen = datetime("now") WHERE id = ?',
                (status, asset['id'])
            )

            if status == '异常':
                results['异常'] += 1
            else:
                results['无异常'] += 1

            # 打印结果
            note_str = f" - {note}" if note else ""
            print(f"    -> {status}{note_str}")

            # 延迟
            time.sleep(self.delay)

        conn.commit()
        conn.close()

        results['total'] = len(assets)
        return results

    def get_stats(self) -> Dict[str, int]:
        """获取检测统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {'总数': 0, '未检测': 0, '异常': 0, '无异常': 0}

        cursor.execute('SELECT status, COUNT(*) FROM assets GROUP BY status')
        for row in cursor.fetchall():
            stats[row[0]] = row[1]
            stats['总数'] += row[1]

        conn.close()
        return stats


def run_cli():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='资产检测工具')
    parser.add_argument('--limit', type=int, default=100, help='每次检测条数')
    parser.add_argument('--db', type=str, default=None, help='数据库路径')
    args = parser.parse_args()

    db_path = args.db or os.path.join(os.path.dirname(__file__), '..', 'database', 'assets.db')

    detector = Detector(db_path)

    print("=" * 60)
    print("资产检测模块")
    print("=" * 60)

    # 显示统计
    stats = detector.get_stats()
    print(f"\n当前状态统计: {stats}")

    # 执行检测
    results = detector.detect_batch(limit=args.limit)

    print(f"\n检测完成: {results}")
    print("=" * 60)


if __name__ == "__main__":
    run_cli()
