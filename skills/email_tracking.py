"""
Skill 5: 邮件追踪 (Email Tracking)
─────────────────────────────────
SMTP直发 + 1x1追踪像素(已读检测) + 退信拦截 + 客户回复意图分类
"""


class EmailTrackingSkill:
    name = "邮件追踪"
    name_en = "Email Tracking"
    description = "SMTP直发(QQ/Gmail) + 追踪像素已读检测 + 退信智能拦截 + 客户回复意图AI分类(8类)"
    version = "1.0"
    tools = ["send_email", "check_email_status"]
    providers = ["mailer.py", "email_tracker.py", "smtp_config.py"]

    INTENT_CATEGORIES = [
        "inquiry", "price_negotiation", "sample_request",
        "order_confirmed", "rejection", "logistics",
        "after_sales", "other",
    ]

    @staticmethod
    def get_rules():
        return """
# 邮件追踪规则
- SMTP发送成功后自动嵌入追踪像素（1x1透明GIF）
- 客户打开邮件 → 记录打开时间+IP+UserAgent
- 退信自动拦截 → 标记 ❌不可用
- 客户回复 → AI分类意图（询价/议价/索样/下单/拒绝/物流/售后）
- 3天未回复自动提醒跟进
"""
