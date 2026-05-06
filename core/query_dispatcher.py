#!/usr/bin/env python3
"""
多平台查询调度器
- 读取配置中的账号列表
- 按分页范围分配给各账号
- 汇总结果
- 支持从Excel加载关键词任务
"""

import yaml
from typing import List, Dict, Any, Optional
from platforms.hunter import HunterClient, assign_pages_to_accounts
from core.keyword_expander import parse_excel_keywords, expand_keyword


class QueryDispatcher:
    """查询调度器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.hunter_keys = self.config['hunter']['api_keys']
        self.github_tokens = self.config['github']['tokens']
        
        self.page_size = self.config['scheduler']['page_size']
        self.delay = self.config['scheduler']['delay_between_requests']
        self.pages_per_account = self.config['scheduler']['max_pages_per_key']
    
    def get_hunter_assignments(self) -> List[Dict[str, Any]]:
        """
        获取 Hunter 账号分页分配
        返回: [{'key': 'api_key', 'start': 1, 'end': 5}, ...]
        """
        assignments = assign_pages_to_accounts(
            num_accounts=len(self.hunter_keys),
            pages_per_account=self.pages_per_account
        )
        
        return [
            {
                'idx': idx,
                'key': key,
                'start_page': start,
                'end_page': end
            }
            for idx, (account_idx, start, end) in enumerate(assignments)
            for key in [self.hunter_keys[account_idx]]
        ]
    
    def dispatch_hunter_query(self, query: str, keyword_name: str) -> List[Dict[str, Any]]:
        """
        分发 Hunter 查询到各账号
        返回所有账号的结果合并
        """
        assignments = self.get_hunter_assignments()
        all_results = []
        
        print(f"\n[Dispatcher] 开始分发 Hunter 查询: {keyword_name}")
        print(f"[Dispatcher] 共有 {len(assignments)} 个账号参与")
        
        for asn in assignments:
            print(f"\n[Dispatcher] 账号 {asn['idx']}: page {asn['start_page']}~{asn['end_page']}")
            
            client = HunterClient(
                api_key=asn['key'],
                page_size=self.page_size,
                delay=self.delay
            )
            
            results = client.search_range(
                query=query,
                start_page=asn['start_page'],
                end_page=asn['end_page']
            )
            
            # 标记来源
            for r in results:
                r['_source_page'] = r.get('page', 0)
                r['_source_key'] = asn['key'][:10] + '...'
            
            all_results.extend(results)
            print(f"[Dispatcher] 账号 {asn['idx']} 获取 {len(results)} 条")
        
        print(f"\n[Dispatcher] 总计获取 {len(all_results)} 条数据")
        return all_results
    
    def get_queries(self) -> List[Dict[str, Any]]:
        """获取启用的查询任务（仅从config.yaml）"""
        return [q for q in self.config['queries'] if q.get('enabled', True)]

    def load_tasks_from_excel(self, excel_path: str) -> List[Dict[str, Any]]:
        """
        从Excel文件加载关键词任务
        Excel格式：关键词 | 任务名称 | 启用状态
        自动生成组合搜索语法
        """
        tasks = parse_excel_keywords(excel_path)
        print(f"[Dispatcher] 从Excel加载 {len(tasks)} 个任务")
        enabled = [t for t in tasks if t['enabled']]
        print(f"[Dispatcher] 启用任务: {len(enabled)} 个")
        return tasks

    def get_enabled_tasks(self, excel_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有启用的任务
        优先从Excel加载，否则从config.yaml
        """
        if excel_path:
            tasks = self.load_tasks_from_excel(excel_path)
            return [t for t in tasks if t['enabled']]
        else:
            return self.get_queries()


if __name__ == "__main__":
    # 测试
    dispatcher = QueryDispatcher()
    
    print("Hunter 分页分配:")
    for asn in dispatcher.get_hunter_assignments():
        print(f"  账号{asn['idx']}: key={asn['key'][:10]}... page={asn['start_page']}~{asn['end_page']}")
    
    print(f"\n启用查询任务:")
    for q in dispatcher.get_queries():
        print(f"  - {q['name']}: {q['keyword']}")