#!/usr/bin/env python3
"""
资产测绘多平台监控系统
主入口

用法:
    python main.py                    # 使用 config.yaml 中的查询
    python main.py --excel keywords.xlsx  # 从Excel加载关键词任务
"""

import os
import sys
import yaml
import argparse

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.query_dispatcher import QueryDispatcher
from core.deduplication import Deduplicator
from core.alert import DingTalkAlert


def load_config():
    """加载配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_query(query_name: str, query_keyword: str, config: dict, deduplicator: Deduplicator,
              search_query: str = None):
    """
    执行单个查询任务
    - query_name: 任务名称
    - query_keyword: 原始关键词（用于存储和追溯）
    - search_query: 完整搜索语法（可与keyword相同，或为组合语法）
    """
    print(f"\n{'='*60}")
    print(f"开始查询: {query_name}")
    print(f"原始关键词: {query_keyword}")
    print(f"搜索语法: {search_query or query_keyword}")
    print(f"{'='*60}")

    # 初始化钉钉告警器
    dingtalk = DingTalkAlert(
        webhook=config['dingtalk']['webhook'],
        secret=config['dingtalk'].get('secret')
    )

    hunter_keys = config['hunter']['api_keys']
    if not hunter_keys:
        print(f"[Error] 没有 Hunter API Key")
        return

    from platforms.hunter import HunterClient

    client = HunterClient(
        api_key=hunter_keys[0],
        page_size=config['scheduler']['page_size'],
        delay=config['scheduler']['delay_between_requests']
    )

    # 使用完整搜索语法（如果有的话）
    actual_query = search_query if search_query else query_keyword

    # 获取总数
    total = client.get_total(actual_query)
    print(f"总数据量: {total}")

    if total == 0:
        print("无数据，跳过")
        return

    # 手动指定分页范围测试（第一个账号 page=1~5）
    pages_per_key = config['scheduler']['max_pages_per_key']
    results = client.search_range(actual_query, start_page=1, end_page=pages_per_key)

    print(f"获取到 {len(results)} 条数据")

    # 去重（source_keyword存原始关键词，方便追溯）
    new_assets = deduplicator.filter_new(results, platform='hunter', source_keyword=query_keyword, source_page=1)
    print(f"新增资产: {len(new_assets)} 条")

    # 告警
    if new_assets:
        dingtalk.alert_assets(new_assets, query_name, 'Hunter', query_keyword)

    print(f"查询完成: {query_name}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='资产测绘监控系统')
    parser.add_argument('--excel', type=str, default=None,
                        help='Excel关键词文件路径（可选）')
    args = parser.parse_args()

    print("Hermès 资产测绘监控系统")
    print("=" * 60)

    # 加载配置
    config = load_config()

    # 初始化去重器
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'assets.db')
    deduplicator = Deduplicator(db_path)

    # 获取统计
    stats = deduplicator.get_stats()
    print(f"数据库已有资产: {stats['total_assets']} 条")
    print(f"已告警资产: {stats['total_alerted']} 条")

    # 初始化调度器
    dispatcher = QueryDispatcher(
        config_path=os.path.join(os.path.dirname(__file__), 'config.yaml')
    )

    # 获取任务（优先从Excel，否则从config.yaml）
    if args.excel:
        excel_path = args.excel
        if not os.path.isabs(excel_path):
            excel_path = os.path.join(os.path.dirname(__file__), excel_path)
        tasks = dispatcher.load_tasks_from_excel(excel_path)
        tasks = [t for t in tasks if t['enabled']]
    else:
        tasks = dispatcher.get_queries()

    if not tasks:
        print("没有启用的查询任务")
        return

    print(f"\n共有 {len(tasks)} 个查询任务")

    for task in tasks:
        if isinstance(task, dict) and 'search_query' in task:
            # 来自Excel的任务（自动扩展语法）
            run_query(
                query_name=task['task_name'],
                query_keyword=task['keyword'],
                config=config,
                deduplicator=deduplicator,
                search_query=task['search_query']
            )
        else:
            # 来自config.yaml的任务
            run_query(
                query_name=task['name'],
                query_keyword=task['keyword'],
                config=config,
                deduplicator=deduplicator
            )

    # 最终统计
    stats = deduplicator.get_stats()
    print(f"\n{'='*60}")
    print("本次运行完成")
    print(f"数据库资产总数: {stats['total_assets']} 条")
    print(f"已告警总数: {stats['total_alerted']} 条")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()