"""
Skill 6: 客户管理 (Contact Management)
─────────────────────────────────────
待联系客户Pipeline：待联系 → 已联系 → 已回复 → 洽谈中 → 已成交 → 关闭
支持多渠道联系记录（邮件/LinkedIn/电话/WhatsApp/展会）
"""


class ContactManagementSkill:
    name = "客户管理"
    name_en = "Contact Management"
    description = "客户Pipeline管理：7种状态流转 + 多渠道联系记录 + 自动提醒 + 统计分析"
    version = "1.0"
    tools = ["db.contacts"]

    CONTACT_METHODS = [
        "email", "linkedin", "phone", "whatsapp",
        "tradeshow", "website_form", "other",
    ]

    STATUS_FLOW = {
        "pending": {"label": "待联系", "next": ["contacted", "invalid"]},
        "contacted": {"label": "已联系", "next": ["replied", "closed"]},
        "replied": {"label": "已回复", "next": ["negotiating", "closed"]},
        "negotiating": {"label": "洽谈中", "next": ["ordered", "closed"]},
        "ordered": {"label": "已成交", "next": []},
        "closed": {"label": "已关闭", "next": ["pending"]},
        "invalid": {"label": "无效", "next": []},
    }

    @staticmethod
    def get_rules():
        return """
# 客户管理规则
- 无邮箱买家自动加入待联系列表
- 支持记录多渠道联系方式
- 设置提醒天数，逾期标橙色
- 7种状态流转：待联系→已联系→已回复→洽谈中→已成交/关闭/无效
"""
