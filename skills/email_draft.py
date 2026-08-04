"""
Skill 2: 开发信撰写与发送 (Email Draft & Send)
─────────────────────────────────────────────
个性化B2B英文开发信生成 + 智能发送策略。
特性：大企业自动拦截 + 推测邮箱风险标注 + SMTP直发/手动双通道
"""


class EmailDraftSkill:
    name = "开发信撰写与发送"
    name_en = "Email Draft & Send"
    description = "个性化B2B开发信生成 + SMTP直发/手动双通道 + 退信智能检测"
    version = "1.0"
    tools = ["draft_email", "send_email"]

    # 推测邮箱前缀黑名单（标注 ⚠️未验证）
    GUESSED_PREFIXES = [
        "purchasing@", "info@", "sales@", "inquiry@",
        "procurement@", "import@", "export@", "contact@",
        "admin@", "office@", "vendors@", "vendor@",
    ]

    @staticmethod
    def get_rules():
        return """
# 开发信规则
- 英文，100字以内，3段：引入→卖点→下一步
- 推测邮箱的邮件前加 [⚠️未验证] 标记
- 发送前必须让用户确认
- 大企业邮箱自动拦截，提示供应商注册
"""
