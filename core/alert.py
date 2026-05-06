#!/usr/bin/env python3
"""
钉钉告警模块
- 同一批次（同一查询条件）合并为1条推送
- Markdown 格式
"""

import json
import hashlib
import hmac
import time
import base64
import urllib.parse
import urllib.request
import ssl
from typing import List, Dict, Any


class DingTalkAlert:
    """钉钉告警器"""
    
    def __init__(self, webhook: str, secret: str = None):
        self.webhook = webhook
        self.secret = secret
    
    def _sign(self, secret: str) -> str:
        """生成签名"""
        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign
    
    def send(self, title: str, text: str, msgtype: str = "markdown") -> bool:
        """发送告警"""
        # 如果有 secret，添加签名
        url = self.webhook
        if self.secret:
            timestamp, sign = self._sign(self.secret)
            url = f"{self.webhook}&timestamp={timestamp}&sign={sign}"
        
        payload = {
            "msgtype": msgtype,
            msgtype: {
                "title": title,
                "text": text
            }
        }
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            resp = urllib.request.urlopen(req, context=ctx, timeout=10)
            result = json.loads(resp.read().decode('utf-8'))
            
            if result.get('errcode') == 0:
                print(f"[DingTalk] 发送成功")
                return True
            else:
                print(f"[DingTalk] 发送失败: {result.get('errmsg')}")
                return False
        except Exception as e:
            print(f"[DingTalk] 发送异常: {e}")
            return False
    
    def alert_assets(self, assets: List[Dict[str, Any]], project: str, 
                     platform: str, keyword: str) -> bool:
        """
        告警新发现的资产
        同一批次合并为1条推送
        """
        if not assets:
            print(f"[DingTalk] 无新资产，跳过告警")
            return True
        
        title = f"🚨 {project} 新增资产"
        
        # 构建 Markdown
        text = f"""## 🚨 新增资产告警

**项目**: {project}
**平台**: {platform}
**查询条件**: {keyword}
**发现时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}

**发现资产（{len(assets)}条）**：
"""
        
        for i, asset in enumerate(assets[:20], 1):  # 最多显示20条
            ip = asset.get('ip', 'N/A')
            port = asset.get('port', 'N/A')
            protocol = asset.get('protocol', 'N/A')
            domain = asset.get('domain', '-')
            title_text = asset.get('web_title', '-') or '-'
            province = asset.get('province', '-')
            city = asset.get('city', '-')
            company = asset.get('company', '-') or '-'
            url = asset.get('url', '-')
            
            # 截断过长的标题和公司名
            if len(title_text) > 25:
                title_text = title_text[:25] + "..."
            if len(company) > 20:
                company = company[:20] + "..."
            
            location = f"{province}{city}" if province != '-' else '-'
            
            text += f"\n{i}. {protocol}://{ip}:{port}"
            text += f"\n   📌 {title_text}"
            text += f"\n   🏢 {company} | 📍 {location}"
            text += f"\n   🔗 {url}"
        
        if len(assets) > 20:
            text += f"\n\n...还有 {len(assets) - 20} 条未显示"
        
        text += f"""

---
*由 Hermès 资产监测系统推送*
"""
        
        return self.send(title, text)


if __name__ == "__main__":
    # 测试
    alert = DingTalkAlert(
        webhook="https://oapi.dingtalk.com/robot/send?access_token=xxx",
        secret="SECxxx"
    )
    
    # 测试数据
    test_assets = [
        {"ip": "1.2.3.4", "port": 443, "domain": "api.test.com", "web_title": "API文档", "protocol": "https"},
        {"ip": "5.6.7.8", "port": 80, "domain": "www.test.com", "web_title": "官网", "protocol": "http"},
    ]
    
    alert.alert_assets(test_assets, "测试项目", "Hunter", 'domain="test.com"')