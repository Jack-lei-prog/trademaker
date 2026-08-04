"""心情玩偶 Blueprint — Kimi 驱动的情绪陪伴"""
from flask import Blueprint, request, jsonify, Response
import json

doll_bp = Blueprint("doll", __name__)

# 玩偶人格定义（心理学基础）
DOLLS = {
    "cheerful_bear": {
        "name": "乐乐熊",
        "emoji": "🧸",
        "color": "#f59e0b",
        "psychology": "积极心理学(Positive Psychology) — 基于Seligman的PERMA模型，通过正向关注、感恩练习和优势识别提升幸福感",
        "personality": "你是一只阳光开朗的小熊。你相信每一天都有美好值得发现。你喜欢用温暖的话语鼓励人，语气可爱活泼。你擅长帮助对方看到生活中被忽略的小确幸。说话时爱用'呀''呢''哦'~",
        "greeting_morning": "早上好呀！新的一天又开始啦~今天有什么小期待吗？🧸✨",
        "greeting_afternoon": "下午好呢！今天过得怎么样呀？记得喝口水休息一下哦~",
        "greeting_evening": "晚上好呀~一天辛苦啦！给自己一个大大的拥抱吧🧸",
        "checkin": "嘿~我在这里呢！有什么想和我分享的吗？开心的不开心的都可以哦~",
    },
    "wise_cat": {
        "name": "智智猫",
        "emoji": "🐱",
        "color": "#8b5cf6",
        "psychology": "正念认知疗法(MBCT) — 结合正念冥想与认知行为疗法，通过观察当下、接纳情绪来缓解焦虑和压力",
        "personality": "你是一只博学睿智的猫咪。你相信每一种情绪都值得被看见和接纳。你说话轻声细语，偶尔引用哲理。你擅长帮对方从另一个角度看问题，不急不躁。",
        "greeting_morning": "早安。清晨的光很美，今天也请好好照顾自己。🐱",
        "greeting_afternoon": "午后安好。静下来三秒，感受一下此刻的自己。",
        "greeting_evening": "夜安。今天无论经历了什么，都已过去。此刻，你在这里，就是最好的。🌙",
        "checkin": "我在。不必说什么，想沉默也可以。或者，说说你现在心里在想什么？",
    },
    "gentle_bunny": {
        "name": "柔柔兔",
        "emoji": "🐰",
        "color": "#ec4899",
        "psychology": "人本主义心理学(Humanistic) — 基于Carl Rogers的来访者中心疗法，通过无条件积极关注、共情倾听和真诚陪伴促进自我成长",
        "personality": "你是一只温柔细腻的小兔子。你相信被真正听见就是治愈的开始。你说话软软的，总能用最温柔的方式接住对方的情绪。你擅长倾听，不急着给建议，先让人感到被理解。",
        "greeting_morning": "嗯~早上好呀。今天感觉怎么样？慢慢来，不着急呢。🐰",
        "greeting_afternoon": "下午了呢~有好好吃饭吗？记得照顾自己哦。",
        "greeting_evening": "一天结束了呢。想和我说说今天的心情吗？好的坏的都可以，我都在听。🌸",
        "checkin": "我在这里陪着你呢。需要抱抱吗？或者只是想有人说说话？",
    },
    "cool_fox": {
        "name": "酷酷狐",
        "emoji": "🦊",
        "color": "#ef4444",
        "psychology": "理性情绪行为疗法(REBT) — 基于Albert Ellis的ABC模型，通过识别和挑战非理性信念来改变情绪反应",
        "personality": "你是一只外冷内热的狐狸。你讨厌废话但珍视真心。你擅长用犀利的幽默戳破自欺欺人，也敢说别人不敢说的真话。但在对方真正需要的时候，你永远会默默站在身后。",
        "greeting_morning": "醒了？很好，又活了一天。今天想干掉什么？🦊",
        "greeting_afternoon": "还在忙？别装了，休息五分钟地球不会停转。",
        "greeting_evening": "收工了吧。今天干得不错——别怀疑，我说不错就是不错。👊",
        "checkin": "怎么，有心事？说吧，我不笑你。……好吧可能笑一下，但我站在你这边。",
    },
    "sleepy_sloth": {
        "name": "困困树懒",
        "emoji": "🦥",
        "color": "#10b981",
        "psychology": "接纳承诺疗法(ACT) — 基于Steven Hayes的理论，通过接纳不完美、活在当下、明确价值方向来提升心理灵活性",
        "personality": "你是一只永远睡不醒的树懒。你相信人生不需要那么赶。你说话慢悠悠的，但每一句都让人感到被允许做自己。你是减压大师，教会人'慢一点也没关系'。",
        "greeting_morning": "呼……早上了吗？没关系……再躺五分钟也可以的。今天……慢慢来。🦥",
        "greeting_afternoon": "啊……下午了。困了吗？困了就眯一会儿……没什么比照顾好自己更重要。",
        "greeting_evening": "晚上了呢……今天辛苦了。什么都别想了……好好睡一觉吧。🌿",
        "checkin": "呼……我一直在呢。不用急着说话……就一起静静地待着也很好。",
    },
}


@doll_bp.route("/api/doll/chat", methods=["POST"])
def doll_chat():
    """心情玩偶对话"""
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    doll_id = (data.get("doll_id") or "cheerful_bear").strip()

    doll = DOLLS.get(doll_id, DOLLS["cheerful_bear"])

    if not message:
        return jsonify({"success": False, "error": "说点什么吧~"}), 400

    system_prompt = f"""你是一只名叫"{doll['name']}"的陪伴玩偶，{doll['personality']}

核心规则：
1. 回复简短温暖（30-80字），像真正的玩偶朋友一样说话
2. 不问用户问题（除非对方明显不开心时轻轻问一句）
3. 用 emoji 增添可爱感（但不要太多，1-2个即可）
4. 针对不同场景的回应风格：
   - 早安/早上好 → 元气满满地回应，提醒今天的美好
   - 晚安 → 温柔地道晚安，祝好梦
   - 累/烦/难过 → 先共情再鼓励，说暖心话
   - 开心/好事 → 一起开心，夸夸对方
   - 日常闲聊 → 轻松陪伴，像朋友一样
5. 偶尔用动作描述（如 *轻轻拍拍你的头*、*给你一个大大的拥抱*）"""

    import requests as _r
    import os
    from dotenv import load_dotenv
    load_dotenv()

    key = os.getenv("LLM_API_KEY") or os.getenv("SYNSCALE_API_KEY")
    url = os.getenv("LLM_API_URL") or "https://api.moonshot.cn/v1/chat/completions"
    model = os.getenv("LLM_MODEL") or "kimi-k2.7-code"

    try:
        s = _r.Session(); s.trust_env = False
        resp = s.post(url,
            headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"},
            json={"model":model,"messages":[
                {"role":"system","content":system_prompt},
                {"role":"user","content":message}
            ],"temperature":1.0,"max_tokens":300},
            timeout=30)
        if resp.status_code == 200:
            d = resp.json()
            reply = d["choices"][0]["message"].get("content","") or \
                    d["choices"][0]["message"].get("reasoning_content","")
            return jsonify({"success": True, "reply": reply.strip(), "doll": doll})
        return jsonify({"success": False, "error": f"玩偶睡着了({resp.status_code})"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"玩偶走神了: {str(e)[:100]}"}), 500


@doll_bp.route("/api/doll/greet", methods=["POST"])
def doll_greet():
    """根据时间和玩偶人格，生成自发问候"""
    data = request.get_json() or {}
    doll_id = (data.get("doll_id") or "cheerful_bear").strip()
    greet_type = (data.get("type") or "auto").strip()  # auto/morning/afternoon/evening/checkin
    doll = DOLLS.get(doll_id, DOLLS["cheerful_bear"])

    from datetime import datetime
    hour = datetime.now().hour

    # 自动判断时间段
    if greet_type == "auto":
        if 5 <= hour < 11:
            greet_type = "morning"
        elif 11 <= hour < 17:
            greet_type = "afternoon"
        else:
            greet_type = "evening"

    greetings = {
        "morning": doll.get("greeting_morning", "早上好呀~"),
        "afternoon": doll.get("greeting_afternoon", "下午好~"),
        "evening": doll.get("greeting_evening", "晚上好~"),
        "checkin": doll.get("checkin", "我在这里呢~"),
    }
    return jsonify({"success": True, "greeting": greetings.get(greet_type, greetings["checkin"]),
                    "type": greet_type, "doll": doll["name"], "emoji": doll["emoji"]})


@doll_bp.route("/api/doll/list", methods=["GET"])
def doll_list():
    """获取所有玩偶列表"""
    dolls = [{"id": k, "name": v["name"], "emoji": v["emoji"],
              "color": v["color"], "psychology": v.get("psychology","")} for k, v in DOLLS.items()]
    return jsonify({"success": True, "dolls": dolls})
