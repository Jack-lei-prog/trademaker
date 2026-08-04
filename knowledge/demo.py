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
    """初始化演示账号（确保密码正确，即使已存在也会更新）"""
    from user_service import _load_users, _save_users, _hash_password

    users = _load_users()
    if DEMO_EMAIL in users:
        # 确保密码哈希正确（修复旧账号密码不匹配问题）
        users[DEMO_EMAIL]["password_hash"] = _hash_password(DEMO_PASSWORD)
        users[DEMO_EMAIL]["product"] = DEMO_PRODUCT
        users[DEMO_EMAIL]["company"] = DEMO_COMPANY
        _save_users(users)
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

DEMO_SCENARIO_DATA = {
    "scenario_1": {
        "title": "场景一：新手卖家找东南亚蓝牙耳机进口商",
        "category": "买家搜索 + 开发信",
        "prompt": "我是深圳蓝牙耳机厂家，想做东南亚市场。帮我搜索新加坡和马来西亚的蓝牙耳机进口商，找到后给每家写一封开发信。",
        "expected": "返回3-5家东南亚买家（含公司名/网站/采购类型/LinkedIn搜索链接），并自动生成英文开发信",
        "sample_buyer": {"company_name": "AudioTech Asia Pte Ltd", "country": "Singapore", "website": "audiotechasia.sg", "product": "TWS Earphones"},
    },
    "scenario_2": {
        "title": "场景二：处理欧洲客户询盘并做合规检查",
        "category": "询盘处理 + 合规",
        "prompt": "收到一封德国客户的询盘：'Dear supplier, we are interested in your ANC bluetooth earphones. Can you send CE/RoHS certificates and FOB price for 5000 units? Regards, Thomas from Berlin Audio GmbH, thomas@berlinaudio.de' 请帮我处理这个询盘。",
        "expected": "自动提取客户信息→分类为真实采购→背景调研→生成英文回复（含CE/RoHS认证和FOB报价）→加入48h跟进",
        "sample_buyer": {"company_name": "Berlin Audio GmbH", "country": "Germany", "email": "thomas@berlinaudio.de", "product": "ANC Bluetooth Earphones"},
    },
    "scenario_3": {
        "title": "场景三：上传厂家Excel列表批量联系",
        "category": "Excel批量 + 客户管理",
        "prompt": "我有一份欧洲客户的Excel表格。请帮我上传表格（点📋按钮），然后针对每家客户分别写开发信。",
        "expected": "上传Excel→解析表格→展示客户列表→选择客户→自动生成个性化开发信→加入客户管理Pipeline",
        "sample_buyer": {"company_name": "Various", "country": "Europe", "count": 5},
    },
}

DEMO_HELP = """
## 📋 TradeMaster 演示指南

**演示账号**: demo@trademaster.com / demo2024
**主营产品**: 蓝牙耳机 (Bluetooth Earphone)

### 3个演示场景（一键操作）

| 场景 | 演示内容 | 时长 |
|------|---------|------|
| 🆕 新手找客户 | 搜索东南亚买家→写开发信 | 1min |
| 🇪🇺 欧洲询盘 | 处理德国客户询盘→合规检查→生成回复 | 1min |
| 📋 批量联系 | 上传Excel→批量开发信→客户管理 | 1min |

### 快速演示路径（3分钟）
1. 登录 → 仪表盘自动展示展销会+认证+统计数据
2. 输入场景提示词 → Agent自动完成全流程
3. 展示左侧展销会面板 + 右侧3D心情玩偶

### 特色功能展示
- 🌓 深色/浅色主题切换
- 📅 展销会情报面板（50+展会数据库）
- 🧸 心情玩偶（5种人格+心理学基础+主动问候）
- 📋 Excel批量处理厂家列表
- 📎 PDF产品手册上传解析
- 🔄 多API故障自动切换
- 🛡️ 大企业邮箱智能拦截
"""
