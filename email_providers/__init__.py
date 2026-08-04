# -*- coding: utf-8 -*-
"""
邮件后端基类 — 定义统一的邮件存储/同步接口
支持 Gmail API / Local JSON 两种实现
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime


class BaseEmailProvider(ABC):
    """邮件后端抽象基类"""

    @abstractmethod
    def record_sent(self, user_email: str, to_email: str, to_name: str,
                    subject: str, body: str, tracking_id: str = "") -> str:
        """记录一封已发送的邮件，返回 email_id"""
        ...

    @abstractmethod
    def get_user_emails(self, user_email: str) -> List[Dict]:
        """获取用户的所有邮件记录"""
        ...

    @abstractmethod
    def get_pending_followups(self, user_email: str) -> List[Dict]:
        """获取待跟进的邮件（>1天未回复）"""
        ...

    @abstractmethod
    def update_status(self, user_email: str, to_email: str, new_status: str) -> Optional[Dict]:
        """更新邮件状态"""
        ...

    @abstractmethod
    def sync_inbox(self, user_email: str) -> List[Dict]:
        """同步收件箱，检测客户回复。返回新发现的回复列表"""
        ...

    @abstractmethod
    def get_stats(self, user_email: str) -> Dict:
        """获取邮件统计数据"""
        ...

    @abstractmethod
    def mark_opened(self, tracking_id: str) -> bool:
        """标记邮件已被打开"""
        ...

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M")
