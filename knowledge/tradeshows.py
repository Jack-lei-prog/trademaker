"""
全球行业展会/展销会知识库
按产品类别索引，包含展会名称、时间、地点、规模、官网
"""
from datetime import datetime

# ============================================================
# 展会数据库（真实展会数据）
# ============================================================
TRADESHOWS = {
    # ── 消费电子 / 蓝牙耳机 / 音频 ──
    "bluetooth earphone": [
        {
            "name": "CES (Consumer Electronics Show)",
            "name_cn": "国际消费电子展",
            "location": "Las Vegas, USA",
            "date": "2027-01-06 ~ 2027-01-09",
            "scale": "180,000+ attendees",
            "focus": "全球最大消费电子展，蓝牙音频品牌必争之地",
            "url": "https://www.ces.tech",
            "tip": "建议提前3个月预约展位并联系北美分销商预约CES期间的见面"
        },
        {
            "name": "IFA Berlin",
            "name_cn": "柏林国际电子消费品展",
            "location": "Berlin, Germany",
            "date": "2026-09-04 ~ 2026-09-09",
            "scale": "240,000+ visitors",
            "focus": "欧洲最大电子展，音频品牌进入欧洲市场的首选平台",
            "url": "https://www.ifa-berlin.com",
            "tip": "欧洲买家注重CE认证和环保包装，参会前确保取得CE/RoHS认证"
        },
        {
            "name": "Global Sources Consumer Electronics",
            "name_cn": "环球资源消费电子展",
            "location": "Hong Kong",
            "date": "2026-10-11 ~ 2026-10-14",
            "scale": "40,000+ buyers",
            "focus": "亚洲最大B2B消费电子采购展，全球蓝牙耳机采购商聚集地",
            "url": "https://www.globalsources.com",
            "tip": "HK展会以OEM/ODM订单为主，建议准备FOB $报价和MOQ清单"
        },
        {
            "name": "HKTDC Hong Kong Electronics Fair",
            "name_cn": "香港秋季电子展",
            "location": "Hong Kong",
            "date": "2026-10-13 ~ 2026-10-16",
            "scale": "67,000+ buyers from 140 countries",
            "focus": "亚洲顶级电子采购展，与环球资源展同期举办",
            "url": "https://www.hktdc.com",
            "tip": "两个HK展会同期，一次行程可覆盖双展，节省差旅成本"
        },
        {
            "name": "MWC Barcelona",
            "name_cn": "世界移动通信大会",
            "location": "Barcelona, Spain",
            "date": "2027-02-28 ~ 2027-03-03",
            "scale": "100,000+ attendees",
            "focus": "移动设备及配件，TWS/ANC蓝牙耳机的重要展示平台",
            "url": "https://www.mwcbarcelona.com",
            "tip": "欧洲电信运营商采购渠道，适合有运营商定制能力的供应商"
        },
    ],
    # ── LED 灯具 / 照明 ──
    "led light": [
        {
            "name": "Light + Building",
            "name_cn": "法兰克福国际灯光照明展",
            "location": "Frankfurt, Germany",
            "date": "2026-10-02 ~ 2026-10-06",
            "scale": "220,000+ visitors",
            "focus": "全球最大照明展，LED灯具出口欧洲的核心渠道",
            "url": "https://www.light-building.com",
            "tip": "欧洲买家对能效标签和环保要求严格，参展前确认ERP/Energy Label合规"
        },
        {
            "name": "Hong Kong International Lighting Fair",
            "name_cn": "香港国际灯饰展",
            "location": "Hong Kong",
            "date": "2026-10-27 ~ 2026-10-30",
            "scale": "38,000+ buyers",
            "focus": "亚洲最大灯饰采购展，LED面板灯/筒灯/太阳能灯需求大",
            "url": "https://www.hktdc.com/hklightingfair",
            "tip": "中东/东南亚买家集中，准备好沙特SASO/东南亚SNI认证可提高成交率"
        },
        {
            "name": "Guangzhou International Lighting Exhibition",
            "name_cn": "广州国际照明展（光亚展）",
            "location": "Guangzhou, China",
            "date": "2026-06-09 ~ 2026-06-12",
            "scale": "160,000+ visitors",
            "focus": "全球LED产业链最全的展会，从芯片到成品全覆盖",
            "url": "https://www.gile-china.com",
            "tip": "国内采购商为主，适合拓展国内渠道和寻找OEM代工客户"
        },
    ],
    # ── 服装 / 纺织 ──
    "clothing": [
        {
            "name": "MAGIC Las Vegas",
            "name_cn": "拉斯维加斯国际服装展",
            "location": "Las Vegas, USA",
            "date": "2026-08-09 ~ 2026-08-11",
            "scale": "80,000+ buyers",
            "focus": "北美最大服装鞋类采购展，快时尚和运动服装品类需求旺盛",
            "url": "https://www.magicfashionevents.com",
            "tip": "美国买家关注交期和MOQ灵活性，准备好FOB Los Angeles报价"
        },
        {
            "name": "Première Vision Paris",
            "name_cn": "巴黎第一视觉面料展",
            "location": "Paris, France",
            "date": "2026-09-14 ~ 2026-09-16",
            "scale": "55,000+ visitors",
            "focus": "全球最高端面料及服装展，欧洲品牌买手集中地",
            "url": "https://www.premierevision.com",
            "tip": "高端路线定位，参展企业需展示可持续面料和环保生产工艺"
        },
    ],
    # ── 家具 / 家居 ──
    "furniture": [
        {
            "name": "Salone del Mobile Milano",
            "name_cn": "米兰国际家具展",
            "location": "Milan, Italy",
            "date": "2027-04-13 ~ 2027-04-18",
            "scale": "370,000+ visitors from 188 countries",
            "focus": "全球最顶级家具设计展，高端家具品牌标杆",
            "url": "https://www.salonemilano.it",
            "tip": "设计驱动型展会，原创设计和环保材料是核心卖点"
        },
        {
            "name": "IMM Cologne",
            "name_cn": "科隆国际家具展",
            "location": "Cologne, Germany",
            "date": "2027-01-17 ~ 2027-01-23",
            "scale": "150,000+ visitors",
            "focus": "欧洲最大B2B家具展，中高端家具出口欧洲的主渠道",
            "url": "https://www.imm-cologne.com",
            "tip": "德国买家重视E1环保标准和FSC认证木材"
        },
    ],
    # ── 手机配件 / 3C 数码 ──
    "phone case": [
        {
            "name": "Global Sources Mobile Electronics",
            "name_cn": "环球资源移动电子展",
            "location": "Hong Kong",
            "date": "2026-10-18 ~ 2026-10-21",
            "scale": "35,000+ buyers",
            "focus": "全球最大手机配件B2B采购展，手机壳/充电宝/数据线/屏幕保护膜",
            "url": "https://www.globalsources.com",
            "tip": "东南亚/中东/南美买家为主，小额批发订单多，推荐准备MOQ 100起报价"
        },
        {
            "name": "CES",
            "name_cn": "国际消费电子展",
            "location": "Las Vegas, USA",
            "date": "2027-01-06 ~ 2027-01-09",
            "scale": "180,000+ attendees",
            "focus": "手机配件新品首发平台，MagSafe/无线充电/环保材料手机壳",
            "url": "https://www.ces.tech",
            "tip": "新品发布窗口，建议携带获得MFi认证（苹果）/ Qi认证（无线充）的样品"
        },
    ],
    # ── 家电 / 小家电 ──
    "home appliance": [
        {
            "name": "IFA Berlin",
            "name_cn": "柏林国际电子消费品展",
            "location": "Berlin, Germany",
            "date": "2026-09-04 ~ 2026-09-09",
            "scale": "240,000+ visitors",
            "focus": "欧洲最大消费电子及家电展，小家电品类齐全",
            "url": "https://www.ifa-berlin.com",
            "tip": "欧洲能效等级A+++产品最受欢迎，提前做ERP测试"
        },
        {
            "name": "Canton Fair Phase 1",
            "name_cn": "广交会第一期（家电）",
            "location": "Guangzhou, China",
            "date": "2026-10-15 ~ 2026-10-19",
            "scale": "200,000+ buyers",
            "focus": "全球最大综合展，家电品类成交量最大的展会",
            "url": "https://www.cantonfair.org.cn",
            "tip": "建议提前2个月邀请老客户来展位，新客户通过广交会官网提前发布产品"
        },
    ],
    # ── 太阳能 / 新能源 ──
    "solar": [
        {
            "name": "Intersolar Europe",
            "name_cn": "慕尼黑国际太阳能展",
            "location": "Munich, Germany",
            "date": "2027-06-14 ~ 2027-06-16",
            "scale": "85,000+ visitors",
            "focus": "全球最大太阳能展，光伏组件/储能/逆变器全产业链",
            "url": "https://www.intersolar.de",
            "tip": "欧洲买家关注TUV认证和碳足迹声明，参展前务必取得相关认证"
        },
        {
            "name": "SNEC PV Power Expo",
            "name_cn": "上海国际太阳能光伏展",
            "location": "Shanghai, China",
            "date": "2027-05-24 ~ 2027-05-26",
            "scale": "500,000+ visitors",
            "focus": "全球最大光伏展，从硅料到组件全链，中东/非洲/拉美采购商集中",
            "url": "https://www.snec.org.cn",
            "tip": "新兴市场买家居多，准备好离网系统和储能解决方案可提高签单率"
        },
    ],
    # ── 玩具 ──
    "toy": [
        {
            "name": "Spielwarenmesse Nuremberg",
            "name_cn": "纽伦堡国际玩具展",
            "location": "Nuremberg, Germany",
            "date": "2027-02-01 ~ 2027-02-05",
            "scale": "70,000+ buyers from 130 countries",
            "focus": "全球最大玩具展，欧洲采购商年度采购节点",
            "url": "https://www.spielwarenmesse.de",
            "tip": "欧洲玩具安全标准EN71是准入门槛，参展前确保取得检测报告"
        },
        {
            "name": "Hong Kong Toys & Games Fair",
            "name_cn": "香港玩具展",
            "location": "Hong Kong",
            "date": "2027-01-11 ~ 2027-01-14",
            "scale": "45,000+ buyers",
            "focus": "亚洲最大玩具展，OEM/ODM订单为主",
            "url": "https://www.hktdc.com/hktoyfair",
            "tip": "与HK Baby Products Fair同期，可一站覆盖玩具+婴童品类"
        },
    ],
    # ── 医疗器械 ──
    "medical device": [
        {
            "name": "MEDICA Düsseldorf",
            "name_cn": "杜塞尔多夫国际医疗展",
            "location": "Düsseldorf, Germany",
            "date": "2026-11-15 ~ 2026-11-18",
            "scale": "120,000+ visitors from 170 countries",
            "focus": "全球最大医疗展，医疗器械/耗材/诊断设备全覆盖",
            "url": "https://www.medica.de",
            "tip": "CE MDR/FDA 510(k)是准入门槛，建议提前6个月申请认证"
        },
        {
            "name": "CMEF Shanghai",
            "name_cn": "中国国际医疗器械博览会",
            "location": "Shanghai, China",
            "date": "2027-04-11 ~ 2027-04-14",
            "scale": "200,000+ visitors",
            "focus": "亚洲最大医疗展，性价比医疗设备和耗材需求大",
            "url": "https://www.cmef.com.cn",
            "tip": "东南亚/中东/非洲买家集中，中低端医疗设备和一次性耗材是主力品类"
        },
    ],
    # ── 化工 ──
    "chemical": [
        {
            "name": "ACHEMA Frankfurt",
            "name_cn": "法兰克福国际化工展",
            "location": "Frankfurt, Germany",
            "date": "2027-06-11 ~ 2027-06-15",
            "scale": "170,000+ visitors",
            "focus": "全球最大化工及生物技术展，精细化工/原料药/实验室设备",
            "url": "https://www.achema.de",
            "tip": "REACH注册是进入欧洲化工市场的前提，展会前确认REACH合规状态"
        },
    ],
}

# ============================================================
# 认证/合规知识库
# ============================================================
CERTIFICATIONS = {
    "bluetooth earphone": [
        {"name": "CE (欧盟)", "required": True, "cost": "¥5,000-15,000", "time": "2-4周", "tip": "出口欧洲强制，含EMC+LVD+RED指令"},
        {"name": "FCC (美国)", "required": True, "cost": "¥3,000-8,000", "time": "2-3周", "tip": "美国FCC ID认证，无线产品强制"},
        {"name": "RoHS (欧盟)", "required": True, "cost": "¥1,000-3,000", "time": "1周", "tip": "有害物质限制，几乎所有出口产品需要"},
        {"name": "BQB (蓝牙)", "required": False, "cost": "¥8,000-20,000", "time": "4-6周", "tip": "蓝牙SIG认证，大客户通常要求"},
    ],
    "led light": [
        {"name": "CE+ERP (欧盟)", "required": True, "cost": "¥8,000-20,000", "time": "3-6周", "tip": "能效标签强制，ERP指令要求能效等级A以上"},
        {"name": "UL/ETL (美国)", "required": True, "cost": "¥15,000-50,000", "time": "6-12周", "tip": "美国安全认证，LED灯具进入北美市场强制"},
        {"name": "SASO (沙特)", "required": True, "cost": "¥5,000-10,000", "time": "2-4周", "tip": "出口沙特强制，需配合SABER系统注册"},
    ],
    "clothing": [
        {"name": "OEKO-TEX 100", "required": True, "cost": "¥3,000-8,000", "time": "2-3周", "tip": "纺织品有害物质检测，欧洲买家基本要求"},
        {"name": "GOTS (有机棉)", "required": False, "cost": "¥10,000-30,000", "time": "4-8周", "tip": "全球有机纺织品标准，可持续时尚卖家关注"},
    ],
    "toy": [
        {"name": "EN71 (欧盟)", "required": True, "cost": "¥5,000-15,000", "time": "3-6周", "tip": "欧洲玩具安全标准，物理+化学+可燃性测试"},
        {"name": "ASTM F963 (美国)", "required": True, "cost": "¥5,000-12,000", "time": "3-6周", "tip": "美国玩具安全标准，CPSIA合规"},
        {"name": "CCC (中国3C)", "required": True, "cost": "¥3,000-8,000", "time": "4-8周", "tip": "电玩具/塑胶玩具进入中国市场强制认证"},
    ],
    "medical device": [
        {"name": "CE MDR (欧盟)", "required": True, "cost": "¥50,000-300,000", "time": "6-18个月", "tip": "欧盟医疗器械法规，2021年升级版，比旧MDD更严格"},
        {"name": "FDA 510(k) (美国)", "required": True, "cost": "¥30,000-200,000", "time": "3-12个月", "tip": "美国医疗器械上市许可"},
        {"name": "ISO 13485", "required": True, "cost": "¥15,000-40,000", "time": "3-6个月", "tip": "医疗器械质量管理体系，全球通用"},
    ],
    "solar": [
        {"name": "TÜV Rheinland (德国)", "required": True, "cost": "¥30,000-100,000", "time": "2-4个月", "tip": "光伏组件认证，欧洲市场强制要求"},
        {"name": "IEC 61215/61730", "required": True, "cost": "¥50,000-150,000", "time": "3-6个月", "tip": "光伏组件安全和性能国际标准"},
    ],
}


# ============================================================
# 匹配引擎
# ============================================================

def _parse_tradeshow_date_range(date_str: str):
    """Parse date range like '2026-10-11 ~ 2026-10-14', returns (start, end) or None"""
    import re
    parts = re.split(r'\s*[~\-]+\s*', date_str.replace('~', '-'), maxsplit=1)
    try:
        start = datetime.strptime(parts[0].strip(), '%Y-%m-%d').date()
        end = datetime.strptime(parts[1].strip(), '%Y-%m-%d').date() if len(parts) > 1 else start
        return start, end
    except (ValueError, IndexError):
        return None, None


def _enrich_tradeshow(show: dict, product_key: str) -> dict:
    """Add source metadata and status to a tradeshow entry"""
    start, end = _parse_tradeshow_date_range(show.get('date', ''))
    today = datetime.now().date()
    if end and end < today:
        status = 'ended'
    elif start and start > today:
        status = 'upcoming'
    elif start and start <= today <= end:
        status = 'ongoing'
    else:
        status = 'unknown'

    return {
        **show,
        'source': show.get('source', 'Manual curation'),
        'source_url': show.get('url', ''),
        'last_verified': show.get('last_verified', '2026-08-07'),
        'start_date': start.isoformat() if start else None,
        'end_date': end.isoformat() if end else None,
        'status': status,
        'product_category': product_key,
    }


def find_tradeshows(product_keywords: str, top_n: int = 5, include_expired: bool = False) -> list:
    """
    根据产品关键词匹配相关展会。
    支持中英文关键词模糊匹配。
    """
    if not product_keywords:
        return []

    lower = product_keywords.lower()
    scored = []

    for key, shows in TRADESHOWS.items():
        # 计算匹配度
        score = 0
        key_parts = key.split()
        for part in key_parts:
            if part in lower:
                score += 3
        # 尝试中文映射
        cn_map = {
            "蓝牙": "bluetooth", "耳机": "earphone", "耳塞": "earphone",
            "led": "led", "灯": "light", "照明": "light",
            "服装": "clothing", "衣服": "clothing", "纺织": "clothing",
            "家具": "furniture", "家居": "furniture", "沙发": "furniture",
            "手机壳": "phone case", "手机套": "phone case", "3c": "phone case",
            "家电": "home appliance", "电器": "home appliance",
            "太阳能": "solar", "光伏": "solar", "新能源": "solar",
            "玩具": "toy",
            "医疗": "medical device", "器械": "medical device",
            "化工": "chemical",
            "配件": "phone case",
        }
        for cn, en in cn_map.items():
            if cn in lower and en == key:
                score += 2
            elif cn in lower and en in key:
                score += 1

        if score > 0:
            # 过滤已过期展会
            filtered = []
            for show in shows:
                enriched = _enrich_tradeshow(show, key)
                if include_expired or enriched['status'] != 'ended':
                    filtered.append(enriched)
            if filtered or include_expired:
                scored.append((score, key, filtered))

    # 按匹配度排序
    scored.sort(key=lambda x: x[0], reverse=True)

    # 如果全都不匹配，返回通用展会
    if not scored:
        general = [
            {
                "name": "Canton Fair",
                "name_cn": "广交会",
                "location": "Guangzhou, China",
                "date": "每年4月/10月",
                "scale": "200,000+ buyers",
                "focus": f"全球最大综合展，覆盖各品类，适合推广'{product_keywords}'类产品",
                "url": "https://www.cantonfair.org.cn",
                "tip": "综合性展会，适合多品类供应商，单个品类建议配合专业展效果更好"
            },
            {
                "name": "Global Sources",
                "name_cn": "环球资源展",
                "location": "Hong Kong",
                "date": "每年4月/10月",
                "scale": "40,000+ buyers",
                "focus": "亚洲B2B出口采购展，覆盖消费电子/家居/礼品/服装等",
                "url": "https://www.globalsources.com",
                "tip": "HK展会买家质量较高，适合寻找OEM/ODM订单"
            },
        ]
        return general

    # 合并匹配到的展会并去重
    seen = set()
    results = []
    for _, key, shows in scored:
        for s in shows:
            if s["name"] not in seen:
                seen.add(s["name"])
                results.append(s)
    return results[:top_n]


def find_certifications(product_keywords: str) -> list:
    """根据产品关键词匹配相关认证要求"""
    if not product_keywords:
        return []
    lower = product_keywords.lower()
    for key, certs in CERTIFICATIONS.items():
        if key in lower or any(k in lower for k in key.split()):
            return certs
    return []


def get_market_tips(product_keywords: str) -> list:
    """根据产品类型返回市场建议"""
    tips = {
        "bluetooth earphone": [
            "2026年全球TWS耳机市场规模预计$150B+，ANC主动降噪和低延迟是核心卖点",
            "北美/欧洲为主要市场(占65%)，东南亚增速最快(年增18%)",
            "亚马逊Best Seller蓝牙耳机均价$35，利润空间在成本$8-15的产品",
            "建议定价策略：成本x3=批发价，批发价x3=零售价"
        ],
        "led light": [
            "全球LED照明市场2026年预计$85B，年增长率12%",
            "欧洲能效指令ERP强制A级能效，低能效产品将被逐出市场",
            "智能照明(APP控制/WiFi/Zigbee)是增长最快的细分",
            "太阳能LED灯在非洲/东南亚市场爆发式增长"
        ],
        "clothing": [
            "可持续时尚是欧洲市场核心趋势，再生聚酯/有机棉面料需求激增",
            "快时尚MOQ门槛降低到100件/款，小单快反成为可能",
            "DTC品牌崛起，传统批发模式正在被独立站+社交媒体模式取代"
        ],
        "solar": [
            "2026全球光伏新增装机预计500GW+，中东/非洲增速超50%",
            "欧洲碳边境税CBAM 2026年正式实施，低碳足迹组件有竞争优势",
            "储能+光伏的混合系统是中东北非最热门品类"
        ],
    }
    lower = product_keywords.lower()
    for key, t in tips.items():
        if key in lower or any(k in lower for k in key.split()):
            return t
    return [
        f"建议关注 {product_keywords} 品类在亚马逊/阿里巴巴国际站的搜索趋势",
        "关注目标市场的最新进口政策和关税变动",
        "参加行业展会是获取一手客户资源的最快方式"
    ]


# ============================================================
# 展会参展商搜索链接
# ============================================================
def get_exhibitor_search_urls(product: str) -> list:
    """根据产品返回主要展会的参展商名录搜索链接"""
    encoded = product.replace(" ", "%20")
    return [
        {
            "name": "CES Exhibitor Directory",
            "url": f"https://www.ces.tech/exhibitor-directory.aspx",
            "tip": "搜索电子产品类参展商，包含联系方式"
        },
        {
            "name": "IFA Berlin Exhibitors",
            "url": f"https://www.ifa-berlin.com/exhibitors-products/",
            "tip": "消费电子+家电参展商，欧洲市场为主"
        },
        {
            "name": f"Alibaba.com RFQ — {product}",
            "url": f"https://www.alibaba.com/trade/search?spm=a2700.galleryofferlist.rfq_search&IndexArea=rfq_en&SearchText={encoded}",
            "tip": "实时采购需求，可直接报价"
        },
        {
            "name": f"LinkedIn — {product} Buyers",
            "url": f"https://www.linkedin.com/search/results/people/?keywords={encoded}%20buyer%20OR%20purchasing",
            "tip": "搜索采购经理和sourcing工程师"
        },
        {
            "name": f"Google — {product} Importers",
            "url": f"https://www.google.com/search?q={encoded}+importer+OR+distributor",
            "tip": "搜索全球进口商和分销商"
        },
    ]
