# -*- coding: utf-8 -*-
"""
Clarity 通知服务
================

支持多渠道推送：
- 企业微信机器人 (WeChat Work)
- 飞书机器人 (Feishu/Lark)
- Telegram Bot
- 邮件通知 (SMTP)
- 自定义 Webhook（支持钉钉、Discord、Slack、Bark 等）
- Pushover（iOS/Android 推送）
"""

from __future__ import annotations

import json
import logging
import os
import re
import smtplib
import time
from dataclasses import dataclass, field
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import requests

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """通知渠道类型"""
    WECHAT = "wechat"       # 企业微信
    FEISHU = "feishu"       # 飞书
    TELEGRAM = "telegram"   # Telegram
    EMAIL = "email"         # 邮件
    PUSHOVER = "pushover"   # Pushover（手机/桌面推送）
    CUSTOM = "custom"       # 自定义 Webhook


# SMTP 服务器配置（自动识别）
SMTP_CONFIGS = {
    "qq.com": {"server": "smtp.qq.com", "port": 465, "ssl": True},
    "foxmail.com": {"server": "smtp.qq.com", "port": 465, "ssl": True},
    "163.com": {"server": "smtp.163.com", "port": 465, "ssl": True},
    "126.com": {"server": "smtp.126.com", "port": 465, "ssl": True},
    "gmail.com": {"server": "smtp.gmail.com", "port": 587, "ssl": False},
    "outlook.com": {"server": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "hotmail.com": {"server": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "aliyun.com": {"server": "smtp.aliyun.com", "port": 465, "ssl": True},
    "sina.com": {"server": "smtp.sina.com", "port": 465, "ssl": True},
}


@dataclass
class NotificationConfig:
    """通知服务配置"""
    # 企业微信
    wechat_webhook_url: str | None = None
    wechat_max_bytes: int = 4000
    
    # 飞书
    feishu_webhook_url: str | None = None
    feishu_max_bytes: int = 20000
    
    # Telegram
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    
    # 邮件
    email_sender: str | None = None
    email_password: str | None = None
    email_receivers: list[str] = field(default_factory=list)
    
    # Pushover
    pushover_user_key: str | None = None
    pushover_api_token: str | None = None
    
    # 自定义 Webhook
    custom_webhook_urls: list[str] = field(default_factory=list)
    custom_webhook_bearer_token: str | None = None
    
    @classmethod
    def from_env(cls) -> "NotificationConfig":
        """从环境变量加载配置"""
        receivers_str = os.getenv("EMAIL_RECEIVERS", "")
        receivers = [r.strip() for r in receivers_str.split(",") if r.strip()]
        
        custom_urls_str = os.getenv("CUSTOM_WEBHOOK_URLS", "")
        custom_urls = [u.strip() for u in custom_urls_str.split(",") if u.strip()]
        
        return cls(
            # 企业微信
            wechat_webhook_url=os.getenv("WECHAT_WEBHOOK_URL"),
            wechat_max_bytes=int(os.getenv("WECHAT_MAX_BYTES", "4000")),
            # 飞书
            feishu_webhook_url=os.getenv("FEISHU_WEBHOOK_URL"),
            feishu_max_bytes=int(os.getenv("FEISHU_MAX_BYTES", "20000")),
            # Telegram
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            # 邮件
            email_sender=os.getenv("EMAIL_SENDER"),
            email_password=os.getenv("EMAIL_PASSWORD"),
            email_receivers=receivers or ([os.getenv("EMAIL_SENDER")] if os.getenv("EMAIL_SENDER") else []),
            # Pushover
            pushover_user_key=os.getenv("PUSHOVER_USER_KEY"),
            pushover_api_token=os.getenv("PUSHOVER_API_TOKEN"),
            # 自定义 Webhook
            custom_webhook_urls=custom_urls,
            custom_webhook_bearer_token=os.getenv("CUSTOM_WEBHOOK_BEARER_TOKEN"),
        )


class NotificationService:
    """
    通知服务
    
    支持多渠道推送：
    - 企业微信 Webhook
    - 飞书 Webhook
    - Telegram Bot
    - 邮件 SMTP
    - Pushover（手机/桌面推送）
    - 自定义 Webhook（钉钉、Discord、Slack、Bark 等）
    """
    
    def __init__(self, config: NotificationConfig | None = None):
        """初始化通知服务"""
        self.config = config or NotificationConfig.from_env()
        self._available_channels = self._detect_channels()
        
        if self._available_channels:
            names = [self._get_channel_name(ch) for ch in self._available_channels]
            logger.info(f"已配置 {len(self._available_channels)} 个通知渠道：{', '.join(names)}")
        else:
            logger.warning("未配置有效的通知渠道")
    
    def _detect_channels(self) -> list[NotificationChannel]:
        """检测已配置的渠道"""
        channels = []
        
        if self.config.wechat_webhook_url:
            channels.append(NotificationChannel.WECHAT)
        if self.config.feishu_webhook_url:
            channels.append(NotificationChannel.FEISHU)
        if self.config.telegram_bot_token and self.config.telegram_chat_id:
            channels.append(NotificationChannel.TELEGRAM)
        if self.config.email_sender and self.config.email_password:
            channels.append(NotificationChannel.EMAIL)
        if self.config.pushover_user_key and self.config.pushover_api_token:
            channels.append(NotificationChannel.PUSHOVER)
        if self.config.custom_webhook_urls:
            channels.append(NotificationChannel.CUSTOM)
        
        return channels
    
    @staticmethod
    def _get_channel_name(channel: NotificationChannel) -> str:
        """获取渠道中文名称"""
        names = {
            NotificationChannel.WECHAT: "企业微信",
            NotificationChannel.FEISHU: "飞书",
            NotificationChannel.TELEGRAM: "Telegram",
            NotificationChannel.EMAIL: "邮件",
            NotificationChannel.PUSHOVER: "Pushover",
            NotificationChannel.CUSTOM: "自定义Webhook",
        }
        return names.get(channel, "未知")
    
    def is_available(self) -> bool:
        """检查通知服务是否可用"""
        return len(self._available_channels) > 0
    
    def get_available_channels(self) -> list[NotificationChannel]:
        """获取所有已配置的渠道"""
        return self._available_channels
    
    def get_channel_names(self) -> str:
        """获取所有已配置渠道的名称"""
        return ", ".join([self._get_channel_name(ch) for ch in self._available_channels])
    
    # ========== 企业微信 ==========
    
    def send_to_wechat(self, content: str) -> bool:
        """推送消息到企业微信机器人"""
        if not self.config.wechat_webhook_url:
            logger.warning("企业微信 Webhook 未配置")
            return False
        
        max_bytes = self.config.wechat_max_bytes
        content_bytes = len(content.encode("utf-8"))
        
        if content_bytes > max_bytes:
            logger.info(f"消息超长({content_bytes}字节)，分批发送")
            return self._send_chunked(
                content, max_bytes,
                lambda chunk: self._post_wechat(chunk)
            )
        
        return self._post_wechat(content)
    
    def _post_wechat(self, content: str) -> bool:
        """发送单条企业微信消息"""
        try:
            payload = {
                "msgtype": "markdown",
                "markdown": {"content": content}
            }
            resp = requests.post(
                self.config.wechat_webhook_url,
                json=payload,
                timeout=10
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info("企业微信消息发送成功")
                    return True
                logger.error(f"企业微信返回错误: {result}")
            else:
                logger.error(f"企业微信请求失败: HTTP {resp.status_code}")
            return False
        except Exception as e:
            logger.error(f"发送企业微信消息失败: {e}")
            return False
    
    # ========== 飞书 ==========
    
    def send_to_feishu(self, content: str) -> bool:
        """推送消息到飞书机器人"""
        if not self.config.feishu_webhook_url:
            logger.warning("飞书 Webhook 未配置")
            return False
        
        formatted = self._format_feishu_markdown(content)
        max_bytes = self.config.feishu_max_bytes
        content_bytes = len(formatted.encode("utf-8"))
        
        if content_bytes > max_bytes:
            logger.info(f"飞书消息超长({content_bytes}字节)，分批发送")
            return self._send_chunked(
                formatted, max_bytes,
                lambda chunk: self._post_feishu(chunk)
            )
        
        return self._post_feishu(formatted)
    
    def _post_feishu(self, content: str) -> bool:
        """发送单条飞书消息（使用交互卡片）"""
        try:
            # 优先使用 Markdown 卡片
            payload = {
                "msg_type": "interactive",
                "card": {
                    "config": {"wide_screen_mode": True},
                    "header": {
                        "title": {"tag": "plain_text", "content": "Clarity 分析报告"}
                    },
                    "elements": [
                        {"tag": "div", "text": {"tag": "lark_md", "content": content}}
                    ]
                }
            }
            
            resp = requests.post(
                self.config.feishu_webhook_url,
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                result = resp.json()
                code = result.get("code") or result.get("StatusCode", 0)
                if code == 0:
                    logger.info("飞书消息发送成功")
                    return True
                logger.error(f"飞书返回错误: {result}")
            else:
                logger.error(f"飞书请求失败: HTTP {resp.status_code}")
            
            # 回退到纯文本
            fallback_payload = {
                "msg_type": "text",
                "content": {"text": content}
            }
            resp = requests.post(
                self.config.feishu_webhook_url,
                json=fallback_payload,
                timeout=30
            )
            return resp.status_code == 200 and resp.json().get("code", -1) == 0
            
        except Exception as e:
            logger.error(f"发送飞书消息失败: {e}")
            return False
    
    def _format_feishu_markdown(self, content: str) -> str:
        """转换 Markdown 为飞书 lark_md 格式"""
        lines = []
        for line in content.splitlines():
            # 标题转加粗
            if re.match(r"^#{1,6}\s+", line):
                title = re.sub(r"^#{1,6}\s+", "", line).strip()
                line = f"**{title}**" if title else ""
            # 引用
            elif line.startswith("> "):
                line = f"💬 {line[2:].strip()}"
            # 分隔线
            elif line.strip() == "---":
                line = "────────"
            # 列表
            elif line.startswith("- "):
                line = f"• {line[2:].strip()}"
            lines.append(line)
        return "\n".join(lines)
    
    # ========== Telegram ==========
    
    def send_to_telegram(self, content: str) -> bool:
        """推送消息到 Telegram"""
        if not self.config.telegram_bot_token or not self.config.telegram_chat_id:
            logger.warning("Telegram 配置不完整")
            return False
        
        api_url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
        max_length = 4096
        
        if len(content) <= max_length:
            return self._post_telegram(api_url, content)
        
        # 分段发送
        return self._send_chunked(
            content, max_length,
            lambda chunk: self._post_telegram(api_url, chunk),
            use_bytes=False
        )
    
    def _post_telegram(self, api_url: str, content: str) -> bool:
        """发送单条 Telegram 消息"""
        try:
            # 转换 Markdown
            tg_content = self._convert_telegram_markdown(content)
            
            payload = {
                "chat_id": self.config.telegram_chat_id,
                "text": tg_content,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            resp = requests.post(api_url, json=payload, timeout=10)
            
            if resp.status_code == 200 and resp.json().get("ok"):
                logger.info("Telegram 消息发送成功")
                return True
            
            # 如果 Markdown 解析失败，用纯文本重试
            payload["text"] = content
            del payload["parse_mode"]
            resp = requests.post(api_url, json=payload, timeout=10)
            return resp.status_code == 200 and resp.json().get("ok")
            
        except Exception as e:
            logger.error(f"发送 Telegram 消息失败: {e}")
            return False
    
    def _convert_telegram_markdown(self, text: str) -> str:
        """转换为 Telegram Markdown 格式"""
        result = text
        result = re.sub(r"^#{1,6}\s+", "", result, flags=re.MULTILINE)
        result = re.sub(r"\*\*(.+?)\*\*", r"*\1*", result)
        for char in ["[", "]", "(", ")"]:
            result = result.replace(char, f"\\{char}")
        return result
    
    # ========== 邮件 ==========
    
    def send_to_email(self, content: str, subject: str | None = None) -> bool:
        """通过 SMTP 发送邮件"""
        if not self.config.email_sender or not self.config.email_password:
            logger.warning("邮件配置不完整")
            return False
        
        sender = self.config.email_sender
        receivers = self.config.email_receivers or [sender]
        
        try:
            if subject is None:
                date_str = datetime.now().strftime("%Y-%m-%d")
                subject = f"📊 Clarity 分析报告 - {date_str}"
            
            # 转换为 HTML
            html_content = self._markdown_to_html(content)
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = Header(subject, "utf-8")
            msg["From"] = sender
            msg["To"] = ", ".join(receivers)
            
            msg.attach(MIMEText(content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            # 自动识别 SMTP 配置
            domain = sender.split("@")[-1].lower()
            smtp_config = SMTP_CONFIGS.get(domain, {
                "server": f"smtp.{domain}",
                "port": 465,
                "ssl": True
            })
            
            if smtp_config["ssl"]:
                server = smtplib.SMTP_SSL(smtp_config["server"], smtp_config["port"], timeout=30)
            else:
                server = smtplib.SMTP(smtp_config["server"], smtp_config["port"], timeout=30)
                server.starttls()
            
            server.login(sender, self.config.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"邮件发送成功，收件人: {receivers}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("邮件认证失败，请检查邮箱和授权码")
            return False
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    def _markdown_to_html(self, md: str) -> str:
        """Markdown 转 HTML"""
        html = md
        html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        html = re.sub(r"^---$", r"<hr>", html, flags=re.MULTILINE)
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = html.replace("\n", "<br>\n")
        
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }}
h1, h2, h3 {{ color: #333; }} hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
</style></head><body>{html}</body></html>"""
    
    # ========== Pushover ==========
    
    def send_to_pushover(self, content: str, title: str | None = None) -> bool:
        """推送消息到 Pushover"""
        if not self.config.pushover_user_key or not self.config.pushover_api_token:
            logger.warning("Pushover 配置不完整")
            return False
        
        api_url = "https://api.pushover.net/1/messages.json"
        
        if title is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            title = f"📊 Clarity 报告 - {date_str}"
        
        # Pushover 限制 1024 字符
        plain_content = self._markdown_to_plain(content)
        max_length = 1024
        
        if len(plain_content) <= max_length:
            return self._post_pushover(api_url, plain_content, title)
        
        return self._send_chunked(
            plain_content, max_length,
            lambda chunk: self._post_pushover(api_url, chunk, title),
            use_bytes=False
        )
    
    def _post_pushover(self, api_url: str, message: str, title: str) -> bool:
        """发送单条 Pushover 消息"""
        try:
            payload = {
                "token": self.config.pushover_api_token,
                "user": self.config.pushover_user_key,
                "message": message,
                "title": title,
            }
            resp = requests.post(api_url, data=payload, timeout=30)
            
            if resp.status_code == 200 and resp.json().get("status") == 1:
                logger.info("Pushover 消息发送成功")
                return True
            logger.error(f"Pushover 返回错误: {resp.json()}")
            return False
        except Exception as e:
            logger.error(f"发送 Pushover 消息失败: {e}")
            return False
    
    def _markdown_to_plain(self, md: str) -> str:
        """Markdown 转纯文本"""
        text = md
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^[-*]\s+", "• ", text, flags=re.MULTILINE)
        text = re.sub(r"^---+$", "────────", text, flags=re.MULTILINE)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    
    # ========== 自定义 Webhook ==========
    
    def send_to_custom(self, content: str) -> bool:
        """推送消息到自定义 Webhook"""
        if not self.config.custom_webhook_urls:
            logger.warning("未配置自定义 Webhook")
            return False
        
        success_count = 0
        
        for i, url in enumerate(self.config.custom_webhook_urls):
            try:
                payload = self._build_webhook_payload(url, content)
                
                headers = {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "Clarity/1.0",
                }
                if self.config.custom_webhook_bearer_token:
                    headers["Authorization"] = f"Bearer {self.config.custom_webhook_bearer_token}"
                
                resp = requests.post(
                    url,
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    headers=headers,
                    timeout=30
                )
                
                if resp.status_code == 200:
                    logger.info(f"自定义 Webhook {i+1} 推送成功")
                    success_count += 1
                else:
                    logger.error(f"自定义 Webhook {i+1} 失败: HTTP {resp.status_code}")
                    
            except Exception as e:
                logger.error(f"自定义 Webhook {i+1} 异常: {e}")
        
        return success_count > 0
    
    def _build_webhook_payload(self, url: str, content: str) -> dict[str, Any]:
        """根据 URL 构建 Webhook payload"""
        url_lower = url.lower()
        
        # 钉钉
        if "dingtalk" in url_lower or "oapi.dingtalk.com" in url_lower:
            return {
                "msgtype": "markdown",
                "markdown": {"title": "Clarity 报告", "text": content}
            }
        
        # Discord
        if "discord.com/api/webhooks" in url_lower:
            truncated = content[:1900] + "..." if len(content) > 1900 else content
            return {"content": truncated}
        
        # Slack
        if "hooks.slack.com" in url_lower:
            return {"text": content, "mrkdwn": True}
        
        # Bark (iOS)
        if "api.day.app" in url_lower:
            return {"title": "Clarity 报告", "body": content[:4000], "group": "clarity"}
        
        # 通用格式
        return {"text": content, "content": content, "message": content}
    
    # ========== 统一发送 ==========
    
    def send(self, content: str) -> bool:
        """向所有已配置的渠道发送消息"""
        if not self.is_available():
            logger.warning("通知服务不可用")
            return False
        
        logger.info(f"正在向 {len(self._available_channels)} 个渠道发送通知")
        
        success_count = 0
        
        for channel in self._available_channels:
            name = self._get_channel_name(channel)
            try:
                result = False
                if channel == NotificationChannel.WECHAT:
                    result = self.send_to_wechat(content)
                elif channel == NotificationChannel.FEISHU:
                    result = self.send_to_feishu(content)
                elif channel == NotificationChannel.TELEGRAM:
                    result = self.send_to_telegram(content)
                elif channel == NotificationChannel.EMAIL:
                    result = self.send_to_email(content)
                elif channel == NotificationChannel.PUSHOVER:
                    result = self.send_to_pushover(content)
                elif channel == NotificationChannel.CUSTOM:
                    result = self.send_to_custom(content)
                
                if result:
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"{name} 发送失败: {e}")
        
        logger.info(f"通知发送完成：成功 {success_count}/{len(self._available_channels)}")
        return success_count > 0
    
    # ========== 辅助方法 ==========
    
    def _send_chunked(
        self,
        content: str,
        max_size: int,
        send_func: Callable[[str], bool],
        use_bytes: bool = True
    ) -> bool:
        """分批发送长消息"""
        
        def get_size(s: str) -> int:
            return len(s.encode("utf-8")) if use_bytes else len(s)
        
        # 按分隔线分割
        if "\n---\n" in content:
            sections = content.split("\n---\n")
            separator = "\n---\n"
        elif "\n### " in content:
            parts = content.split("\n### ")
            sections = [parts[0]] + [f"### {p}" for p in parts[1:]]
            separator = "\n"
        else:
            sections = content.split("\n")
            separator = "\n"
        
        chunks = []
        current_chunk = []
        current_size = 0
        sep_size = get_size(separator)
        
        for section in sections:
            section_size = get_size(section)
            extra = sep_size if current_chunk else 0
            
            if section_size + extra > max_size:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                # 强制截断超长段
                truncated = self._truncate(section, max_size - 200, use_bytes)
                chunks.append(truncated + "\n...(已截断)")
                continue
            
            if current_size + section_size + extra > max_size:
                chunks.append(separator.join(current_chunk))
                current_chunk = [section]
                current_size = section_size
            else:
                current_chunk.append(section)
                current_size += section_size + extra
        
        if current_chunk:
            chunks.append(separator.join(current_chunk))
        
        total = len(chunks)
        success_count = 0
        
        for i, chunk in enumerate(chunks):
            marker = f"\n\n📄 ({i+1}/{total})" if total > 1 else ""
            if send_func(chunk + marker):
                success_count += 1
            if i < total - 1:
                time.sleep(1)
        
        return success_count == total
    
    def _truncate(self, text: str, max_size: int, use_bytes: bool = True) -> str:
        """截断文本"""
        if use_bytes:
            encoded = text.encode("utf-8")
            if len(encoded) <= max_size:
                return text
            truncated = encoded[:max_size]
            while truncated:
                try:
                    return truncated.decode("utf-8")
                except UnicodeDecodeError:
                    truncated = truncated[:-1]
            return ""
        else:
            return text[:max_size] if len(text) > max_size else text
    
    def save_report(self, content: str, filename: str | None = None) -> Path:
        """保存报告到文件"""
        if filename is None:
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{date_str}.md"
        
        reports_dir = Path(__file__).parent.parent.parent / "runtime" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = reports_dir / filename
        filepath.write_text(content, encoding="utf-8")
        
        logger.info(f"报告已保存到: {filepath}")
        return filepath


# ========== 便捷函数 ==========

def get_notification_service() -> NotificationService:
    """获取通知服务实例"""
    return NotificationService()


def send_notification(content: str) -> bool:
    """发送通知的快捷方式"""
    return get_notification_service().send(content)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    service = NotificationService()
    
    print(f"=== 通知渠道检测 ===")
    print(f"当前渠道: {service.get_channel_names()}")
    print(f"服务可用: {service.is_available()}")
    
    test_content = """
# 📊 每日决策仪表盘
> 生成时间: 2025-01-19 14:30:00

## 🌐 市场概览
| 市场 | 指数 | 涨跌幅 |
|:----:|:----:|:------:|
| A股 | 上证指数 | +1.25% |

## 🏆 今日值得关注
1. **贵州茅台** (600519) - 极具潜力
2. **宁德时代** (300750) - 值得关注

---
*本报告由 Clarity 自动生成*
"""
    
    if service.is_available():
        print("\n=== 推送测试 ===")
        success = service.send(test_content)
        print(f"推送结果: {'成功' if success else '失败'}")
    else:
        print("\n通知渠道未配置，跳过推送测试")
        print("\n配置方式（.env 文件）：")
        print("WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/...")
        print("FEISHU_WEBHOOK_URL=https://open.feishu.cn/...")
        print("TELEGRAM_BOT_TOKEN=xxx")
        print("TELEGRAM_CHAT_ID=xxx")
        print("EMAIL_SENDER=xxx@qq.com")
        print("EMAIL_PASSWORD=xxx")
