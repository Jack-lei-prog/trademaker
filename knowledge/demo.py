"""
Demo 演示系统 — 预置演示账号和示例数据
"""
import os
from datetime import datetime


DEMO_EMAIL = "demo@trademaster.com"
DEMO_PASSWORD = "demo2024"
DEMO_PRODUCT = "bluetooth earphone"
DEMO_COMPANY = "深圳声海科技有限公司"
DEMO_PHONE = "13800138001"


def init_demo_user():
    """初始化演示账号（首次运行时自动创建）"""
    from user_service import _load_users, _save_users, _hash_password

    users = _load_users()
    if DEMO_EMAIL in users:
        return users[DEMO_EMAIL]

    user = {
        "email": DEMO_EMAIL,
        "phone": DEMO_PHONE,
        "company": DEMO_COMPANY,
        "product": DEMO_PRODUCT,
        "identity": "seller",
        "password_hash": _hash_password(DEMO_PASSWORD),
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "last_login": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    users[DEMO_EMAIL] = user
    _save_users(users)

    # 预置示例客户
    _init_sample_contacts()
    return user


def _init_sample_contacts():
    """预置示例待联系客户数据"""
    import db

    samples = [
        {
            "company_name": "AudioPro Distribution GmbH",
            "email": "procurement@audiopro.de",
            "website": "audiopro.de",
            "country": "Germany",
            "product_interest": "ANC蓝牙耳机",
            "contact_method": "email",
            "status": "contacted",
            "notes": "已发送开发信，等待回复。对方是德国前三的音频分销商。",
        },
        {
            "company_name": "SoundWave Imports LLC",
            "email": "",
            "website": "soundwaveimports.com",
            "country": "USA",
            "product_interest": "TWS蓝牙耳机",
            "contact_method": "linkedin",
            "status": "pending",
            "notes": "无邮箱，已通过LinkedIn联系采购经理James Wilson，待回复",
        },
        {
            "company_name": "TechDistribuciones SA",
            "email": "compras@techdistrib.com",
            "website": "techdistrib.com",
            "country": "Mexico",
            "product_interest": "蓝牙耳机+充电盒",
            "contact_method": "whatsapp",
            "status": "replied",
            "notes": "WhatsApp已回复，要求发送FOB报价和MOQ。已发送报价单等待确认。",
        },
    ]

    for s in samples:
        # 避免重复添加
        existing = db.get_contacts(DEMO_EMAIL)
        if not any(c["company_name"] == s["company_name"] for c in existing):
            db.add_contact(
                user_email=DEMO_EMAIL,
                company_name=s["company_name"],
                email=s["email"],
                website=s["website"],
                country=s["country"],
                product_interest=s["product_interest"],
                contact_method=s["contact_method"],
                notes=s.get("notes", ""),
                source="Demo预置",
                next_remind_days=1 if s["status"] == "pending" else 7,
            )
            # 更新状态
            contacts = db.get_contacts(DEMO_EMAIL)
            for c in contacts:
                if c["company_name"] == s["company_name"]:
                    db.update_contact(c["id"], DEMO_EMAIL, status=s["status"])


# ============================================================
# 演示场景脚本
# ============================================================
DEMO_SCENARIOS = [
    {
        "id": 1,
        "title": "场景一：搜索买家并发送开发信",
        "description": "演示从搜索买家到发送开发信的全流程",
        "steps": [
            "使用演示账号登录：demo@trademaster.com / demo2024",
            "登录后自动展示仪表盘：蓝牙耳机相关展销会(CES/IFA/HKTDC)、认证要求(CE/FCC/RoHS)、市场洞察",
            "输入：'帮我搜索德国蓝牙耳机进口商'",
            "Agent返回买家清单（含公司名/国家/邮箱验证状态/采购类型/推荐理由）",
            "点击上下文按钮 → '给XXX写开发信'",
            "Agent生成个性化开发信 → 内联编辑器展示",
            "邮箱会标注验证状态（✅验证 / ⚠️未验证）",
            "选择发送方式：SMTP直发 或 复制后手动发送 → 点'我已手动发送'记录",
            "发送后自动加入跟进队列，显示'3天后未回复将提醒跟进'",
        ],
        "expected_output": "结构化买家清单 + 可发送的开发信 + 跟进记录",
    },
    {
        "id": 2,
        "title": "场景二：处理客户询盘",
        "description": "演示自动处理客户询盘邮件并生成个性化回复",
        "steps": [
            "输入一段模拟询盘：",
            "'Dear supplier, we are TechGlobal Imports from UK, interested in your ANC bluetooth earphones. Could you send us FOB price for 3000 pcs? Our email: james@techglobal-imports.co.uk'",
            "Agent自动调用process_inquiry → 5步闭环处理",
            "展示：客户信息提取结果、意图分类（真实采购/比价/调研/垃圾）、公司背景调研",
            "展示：AI生成的个性化英文回复邮件",
            "确认后发送 → 自动加入48h跟进队列",
        ],
        "expected_output": "客户画像 + 意图分析 + 个性化回复邮件 + 跟进记录",
    },
    {
        "id": 3,
        "title": "场景三：客户管理Pipeline",
        "description": "演示客户联系状态管理和多渠道跟进",
        "steps": [
            "点击顶部'📋 客户跟进'面板",
            "展示预置的3个示例客户（不同状态：待联系/已联系/已回复）",
            "统计栏：总数3 | 待联系1 | 已联系1 | 已回复1",
            "点击SoundWave Imports → 展开详情 → 看到'无邮箱，已通过LinkedIn联系'",
            "点击'✓ 已回复' 更新状态",
            "展示逾期提醒（橙色边框标记）",
        ],
        "expected_output": "客户Pipeline面板 + 状态流转操作 + 统计更新",
    },
]

DEMO_HELP = """
## 📋 TradeMaster 演示指南

**演示账号**: demo@trademaster.com / demo2024
**主营产品**: 蓝牙耳机 (Bluetooth Earphone)

### 快速演示路径（5分钟）

1. **登录** → 自动展示仪表盘（展销会+认证+统计）
2. **搜索买家** → "帮我搜索德国蓝牙耳机进口商"
3. **写开发信** → 点击上下文按钮"给XXX写开发信"
4. **发送邮件** → 复制到剪贴板 / SMTP直发
5. **查看跟进** → 点"📋 客户跟进"面板

### 特色功能展示

- 🌓 深色/浅色主题切换（右上角月亮按钮）
- 📧 SMTP邮箱配置（📧SMTP按钮）
- 📅 登录仪表盘（展销会情报自动匹配）
- 📊 市场洞察（TWS市场规模/定价/趋势）
- 🔄 API故障自动重试队列
- 🛡️ 大企业邮箱自动拦截（试试搜"IKEA买家"）
"""
