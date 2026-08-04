"""
系统提示词构建服务
"""
from prompts import SYSTEM_PROMPT


def build_system_prompt(email=None, session_id="default"):
    from user_service import get_user
    import db
    user = get_user(email) if email else None
    if not user:
        return SYSTEM_PROMPT

    identity = user.get("identity", "seller")
    extra = f"""
# 当前用户信息
- 账号邮箱：{user['email']}
- 联系电话：{user.get('phone', '未填写')}
- 公司名称：{user.get('company', '未填写')}
- 主营产品：{user.get('product', '未填写')}
- 使用身份：{'老板/管理者' if identity == 'boss' else '销售业务员'}
# 重要指令
- 开发信和邮件中，发件人邮箱用 {user['email']}，公司名用 {user.get('company', '我司')}
- 电话署名用 {user.get('phone', '')}
"""

    # 加载产品手册
    metadata = db.get_session_metadata(email, session_id)
    manual = metadata.get("product_manual", "")
    if manual:
        extra += f"""
# 产品手册（已上传）
以下是用户上传的产品手册内容，所有产品相关任务必须基于此手册：
- 写开发信 → 从手册中提取产品卖点、规格、认证、功能
- 写广告语 → 从手册中提取核心卖点和差异化特性
- 生成商品描述 → 从手册中提取技术参数和产品故事
- 回复客户询盘 → 对照手册回答技术问题

---产品手册开始---
{manual[:6000]}
---产品手册结束---

⚠️ 强制规则：当用户要求写开发信/广告语/商品描述/回复客户时，你必须：
1. 从产品手册中提取具体的产品名称、型号、技术参数（芯片/降噪dB/续航/防水等级等）
2. 在文案中直接引用这些具体数据，例如"BT-900 with hybrid ANC -35dB and 40h battery"
3. 引用手册中的认证信息（CE/FCC/RoHS/BQB等）作为信任背书
4. 禁止使用"高品质""卓越性能"等空泛词汇替代具体参数
5. 如果手册有MOQ/FOB价格等商务信息，在回复客户询盘时自动引用
"""

    if identity == 'boss':
        extra += "# 老板模式\n- 侧重整体数据和趋势分析\n- 关注销售报表、团队绩效、市场机会\n- 回复风格简洁高效"
    else:
        extra += f"# 销售模式\n- 侧重开发信撰写、买家搜索、客户跟进\n- 主营产品是 {user.get('product', '')}，主动围绕该产品寻找买家\n- 回复风格热情专业"
    return SYSTEM_PROMPT + "\n" + extra
