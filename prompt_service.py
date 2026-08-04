"""
系统提示词构建服务
"""
from prompts import SYSTEM_PROMPT


def build_system_prompt(email=None):
    from user_service import get_user
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
    if identity == 'boss':
        extra += "# 老板模式\n- 侧重整体数据和趋势分析\n- 关注销售报表、团队绩效、市场机会\n- 回复风格简洁高效"
    else:
        extra += f"# 销售模式\n- 侧重开发信撰写、买家搜索、客户跟进\n- 主营产品是 {user.get('product', '')}，主动围绕该产品寻找买家\n- 回复风格热情专业"
    return SYSTEM_PROMPT + "\n" + extra
