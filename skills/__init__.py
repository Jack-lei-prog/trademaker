"""
TradeMaster Skills Framework
六项核心外贸技能 — 模块化、可插拔、独立可测
"""
from .buyer_search import BuyerSearchSkill
from .email_draft import EmailDraftSkill
from .trade_intelligence import TradeIntelligenceSkill
from .inquiry_processing import InquiryProcessingSkill
from .email_tracking import EmailTrackingSkill
from .contact_management import ContactManagementSkill

SKILLS = {
    "buyer_search": BuyerSearchSkill,
    "email_draft": EmailDraftSkill,
    "trade_intelligence": TradeIntelligenceSkill,
    "inquiry_processing": InquiryProcessingSkill,
    "email_tracking": EmailTrackingSkill,
    "contact_management": ContactManagementSkill,
}

__all__ = ["SKILLS"] + list(SKILLS.keys())
