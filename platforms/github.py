"""
GitHub 平台搜索模块
用于在 GitHub 代码仓库中搜索关键词，发现意外暴露的内部资产

搜索策略：
- 每个关键词搜索: keyword in:file
- 匹配文件内容，对应 Hunter 的 web.body
- Rate Limit: 10次/分钟 (code_search)
"""

import re
import time
import logging
from typing import Generator, Optional
from dataclasses import dataclass, asdict

import requests

logger = logging.getLogger(__name__)

# GitHub API 配置
GITHUB_API = "https://api.github.com"
SEARCH_API = f"{GITHUB_API}/search/code"
HEADERS_BASE = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "AssetMonitor/1.0",
}


@dataclass
class GitHubAsset:
    """GitHub 搜索结果标准化资产"""
    repository: str          # 仓库名 (owner/repo)
    file_path: str          # 文件路径
    sha: str                # 文件 SHA
    url: str                # 代码链接
    match_content: str       # 匹配到的内容片段
    language: str           # 编程语言
    score: float            # 匹配分数
    platform: str = "github"  # 平台标识


class GitHubClient:
    """GitHub 代码搜索客户端"""

    def __init__(self, tokens: list[str]):
        """
        :param tokens: GitHub Personal Access Token 列表，支持多账号轮询
        """
        self.tokens = tokens
        self.token_idx = 0
        self.rate_limit_remaining = 10  # code_search 默认限速
        self.rate_limit_reset = 0       # 限速重置时间戳

    def _get_headers(self) -> dict:
        """生成当前 token 的请求头"""
        headers = HEADERS_BASE.copy()
        headers["Authorization"] = f"token {self._current_token()}"
        return headers

    def _current_token(self) -> str:
        return self.tokens[self.token_idx % len(self.tokens)]

    def _rotate_token(self):
        """轮换到下一个 token"""
        self.token_idx = (self.token_idx + 1) % len(self.tokens)
        logger.info(f"轮换 GitHub Token: idx={self.token_idx}")

    def _wait_if_needed(self):
        """检查限速，必要时等待"""
        import time
        now = time.time()
        if self.rate_limit_remaining <= 1:
            wait_time = self.rate_limit_reset - now + 1
            if wait_time > 0:
                logger.warning(f"GitHub 限速，等待 {wait_time:.0f} 秒")
                time.sleep(wait_time)
            self.rate_limit_remaining = 10  # 重置后恢复

    def _update_rate_limit(self, resp: requests.Response):
        """从响应头更新限速信息"""
        # code_search 限速在 response header 里
        rl = resp.headers.get("X-RateLimit-Remaining")
        rl_reset = resp.headers.get("X-RateLimit-Reset")
        if rl is not None:
            self.rate_limit_remaining = int(rl)
        if rl_reset is not None:
            self.rate_limit_reset = int(rl_reset)

    def search(self, keyword: str, per_page: int = 30) -> dict:
        """
        搜索代码（单次请求）

        :param keyword: 搜索关键词（不需要加引号，API 会自动处理）
        :param per_page: 每页条数，最大 100
        :return: API 原始响应 dict
        """
        self._wait_if_needed()

        url = SEARCH_API
        params = {
            "q": keyword,
            "per_page": min(per_page, 100),
            "page": 1,
        }

        resp = requests.get(
            url,
            params=params,
            headers=self._get_headers(),
            timeout=30,
        )
        self._update_rate_limit(resp)

        if resp.status_code == 401:
            logger.warning(f"Token 无效，轮换: {resp.json().get('message')}")
            self._rotate_token()
            return self.search(keyword, per_page)  # 重试一次

        if resp.status_code == 403:
            error_msg = resp.json().get("message", "")
            if "rate limit" in error_msg.lower():
                logger.warning(f"GitHub 限速: {error_msg}")
                self._rotate_token()
                return self.search(keyword, per_page)

        if resp.status_code != 200:
            logger.error(f"GitHub API 错误 {resp.status_code}: {resp.text[:200]}")
            return {}

        return resp.json()

    def search_paginated(self, keyword: str, max_pages: int = 3) -> Generator[GitHubAsset, None, None]:
        """
        分页搜索，直到没有更多结果或达到最大页数

        :param keyword: 搜索关键词
        :param max_pages: 最大页数（每页30条）
        :yield: GitHubAsset 对象
        """
        page = 1
        total_yielded = 0

        while page <= max_pages:
            self._wait_if_needed()

            params = {
                "q": keyword,
                "per_page": 30,
                "page": page,
            }

            resp = requests.get(
                SEARCH_API,
                params=params,
                headers=self._get_headers(),
                timeout=30,
            )
            self._update_rate_limit(resp)

            if resp.status_code == 403:
                self._rotate_token()
                time.sleep(5)
                continue

            if resp.status_code != 200:
                logger.error(f"搜索失败: {resp.status_code} {resp.text[:100]}")
                break

            data = resp.json()
            items = data.get("items", [])
            total_yielded += len(items)

            for item in items:
                yield self._parse_item(item)

            # 检查是否还有更多结果
            if len(items) < 30:
                break
            if total_yielded >= data.get("total_count", 0):
                break

            page += 1

    def _parse_item(self, item: dict) -> GitHubAsset:
        """解析单个搜索结果为标准资产对象"""
        repo = item.get("repository", {})
        return GitHubAsset(
            repository=repo.get("full_name", ""),
            file_path=item.get("path", ""),
            sha=item.get("sha", ""),
            url=item.get("html_url", ""),
            match_content=self._extract_match_text(item),
            language=repo.get("language", ""),
            score=item.get("score", 0.0),
        )

    def _extract_match_text(self, item: dict) -> str:
        """从 text_matches 中提取匹配片段"""
        text_matches = item.get("text_matches", [])
        if not text_matches:
            return ""
        # 取第一个匹配片段的上下文
        fragment = text_matches[0].get("fragment", "")
        return fragment[:500] if fragment else ""


def build_query(keyword: str, search_type: str = "file") -> str:
    """
    根据关键词构建 GitHub 搜索查询

    :param keyword: 原始关键词
    :param search_type: 搜索类型
        - "file": 搜索文件内容 (默认, 对应 Hunter web.body)
        - "readme": 搜索 README (对应 Hunter title/简介)
        - "test": 搜索测试文件
    :return: GitHub 搜索语法字符串
    """
    # GitHub 搜索语法：关键词 + in:范围
    # 特殊字符需要处理，但 in:file 等修饰符是独立的
    if search_type == "readme":
        return f'{keyword} in:readme'
    elif search_type == "test":
        return f'{keyword} path:test'
    else:  # file (默认)
        return f'{keyword} in:file'


def extract_domains_from_text(text: str) -> list[str]:
    """
    从文本中提取域名

    :param text: 待提取文本（代码片段等）
    :return: 域名列表
    """
    # 匹配常见域名格式
    # 排除常见公共域名
    exclude = {
        "github.com", "githubusercontent.com", "gitlab.com",
        "python.org", "pypi.org", "npmjs.com", "cdnjs.com",
        "google.com", "microsoft.com", "apple.com",
        "baidu.com", "aliyun.com", "tencent.com",
    }
    pattern = r'\b(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b'
    found = re.findall(pattern, text, re.IGNORECASE)
    return [d for d in found if d.lower() not in exclude]


def extract_ips_from_text(text: str) -> list[str]:
    """
    从文本中提取 IPv4 地址

    :param text: 待提取文本
    :return: IP 地址列表
    """
    pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found = re.findall(pattern, text)
    return [ip for ip in found if not ip.startswith("0.")
                                     and not ip.endswith(".0")
                                     and not ip.startswith("255.")]


# ============================================================
# 独立 CLI 测试入口
# ============================================================
if __name__ == "__main__":
    import sys, json, os, yaml

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 加载 config.yaml
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    tokens = config.get("github", {}).get("tokens", [])

    if not tokens:
        print("错误: config.yaml 中未配置 GitHub tokens")
        sys.exit(1)

    client = GitHubClient(tokens)

    keyword = sys.argv[1] if len(sys.argv) > 1 else "电力交易系统"
    print(f"搜索关键词: {keyword}")
    print(f"查询语句: {build_query(keyword)}")

    result = client.search(build_query(keyword))
    print(f"\n总结果数: {result.get('total_count', 0)}")
    print(f"本次返回: {len(result.get('items', []))} 条")

    for item in result.get("items", [])[:3]:
        repo = item.get("repository", {})
        print(f"\n  仓库: {repo.get('full_name')}")
        print(f"  文件: {item.get('path')}")
        print(f"  链接: {item.get('html_url')}")
        matches = item.get("text_matches", [])
        if matches:
            print(f"  匹配片段: {matches[0].get('fragment', '')[:200]}")
