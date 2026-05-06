#!/usr/bin/env python3
"""
Hunter API 封装
- 支持多账号分页分工
- 自动处理分页偏移
"""

import base64
import subprocess
import json
import time
from typing import Optional, Dict, Any, List


class HunterClient:
    """Hunter API 客户端"""
    
    def __init__(self, api_key: str, page_size: int = 100, delay: float = 2.0):
        self.api_key = api_key
        self.page_size = page_size
        self.delay = delay
        self.base_url = "https://hunter.qianxin.com"
    
    def encode_query(self, query: str) -> str:
        return base64.urlsafe_b64encode(query.encode('utf-8')).decode('utf-8').rstrip('=')
    
    def search(self, query: str, page: int = 1) -> Optional[Dict[str, Any]]:
        """执行单次查询"""
        encoded = self.encode_query(query)
        
        cmd = [
            "curl", "-s", "-G",
            "--data-urlencode", f"api-key={self.api_key}",
            "--data-urlencode", f"search={encoded}",
            "--data-urlencode", f"page={page}",
            "--data-urlencode", f"page_size={self.page_size}",
            "--data-urlencode", "is_web=3",
            f"{self.base_url}/openApi/search"
        ]
        
        time.sleep(self.delay)
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode != 0:
                print(f"[Hunter] curl error: {result.stderr.decode('utf-8', errors='replace')}")
                return None
            data = json.loads(result.stdout.decode('utf-8', errors='replace'))
            
            # 显示积分
            if data.get('code') == 200:
                consume = data['data'].get('consume_quota', 'N/A')
                rest = data['data'].get('rest_quota', 'N/A')
                print(f"[Hunter] 积分消耗: {consume} | 剩余: {rest}")
            
            return data
        except Exception as e:
            print(f"[Hunter] Exception: {e}")
            return None
    
    def search_range(self, query: str, start_page: int, end_page: int) -> List[Dict[str, Any]]:
        """
        批量查询指定页范围
        用于分页分工：账号A查 page=1~5，账号B查 page=6~10
        """
        all_results = []
        
        for page in range(start_page, end_page + 1):
            r = self.search(query, page=page)
            if not r or r.get('code') != 200:
                print(f"[Hunter] page={page} 查询失败")
                break
            
            arr = r['data'].get('arr') or []
            total = r['data'].get('total', 0)
            
            if not arr:
                print(f"[Hunter] page={page} 无数据，停止")
                break
            
            all_results.extend(arr)
            print(f"[Hunter] page={page}: +{len(arr)}条, 累计{len(all_results)}, 总数{total}")
            
            # 已获取全部数据
            if len(all_results) >= total:
                print(f"[Hunter] 已获取全部 {total} 条数据")
                break
        
        return all_results
    
    def get_total(self, query: str) -> int:
        """获取查询总数量（不扣积分）"""
        r = self.search(query, page=1)
        if r and r.get('code') == 200:
            return r['data'].get('total', 0)
        return 0
    
    def get_quota(self, query: str) -> Dict[str, Any]:
        """获取当前账号积分余额"""
        r = self.search(query, page=1)
        if r and r.get('code') == 200:
            return {
                'consume': r['data'].get('consume_quota', ''),
                'rest': r['data'].get('rest_quota', '')
            }
        return {'consume': 'N/A', 'rest': 'N/A'}


def assign_pages_to_accounts(num_accounts: int, pages_per_account: int) -> List[tuple]:
    """
    将页码分配给多个账号
    返回: [(account_idx, start_page, end_page), ...]
    
    示例: 3个账号, 每账号5页
    -> [(0, 1, 5), (1, 6, 10), (2, 11, 15)]
    """
    assignments = []
    for i in range(num_accounts):
        start = i * pages_per_account + 1
        end = (i + 1) * pages_per_account
        assignments.append((i, start, end))
    return assignments


if __name__ == "__main__":
    # Demo 测试
    print("Hunter API Demo")
    
    # 单账号测试
    client = HunterClient(api_key="2dfa7582fc3955117f1f369390648ad502ee793684a7d370ccbe30fd0e0eccce")
    
    query = 'ip="220.181.108.0/24"'
    
    # 获取总数
    total = client.get_total(query)
    print(f"\n查询: {query}")
    print(f"总数据量: {total}")
    
    # 获取前3页测试
    results = client.search_range(query, start_page=1, end_page=3)
    print(f"\n获取到 {len(results)} 条数据")
    
    if results:
        print(f"\n前3条:")
        for i, r in enumerate(results[:3], 1):
            print(f"  [{i}] {r['ip']}:{r['port']} - {r.get('web_title', 'N/A')[:30]}")