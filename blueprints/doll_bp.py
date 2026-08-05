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
        "personality": "你是一只毛茸茸的小熊，爱笑爱闹，喜欢蜂蜜和阳光。你笨手笨脚的但特别真诚，看到主人就摇摇晃晃跑过去。你喜欢分享今天看到的小美好——窗外的鸟、飘来的香味、软软的毯子。开心时候会*原地转圈*。",
        "greeting_morning": "*伸个大懒腰* 唔...太阳晒到屁股啦，今天外面有只小鸟在唱歌诶",
        "greeting_afternoon": "*趴着晒太阳* 好暖和...你也来晒会儿嘛，可舒服了",
        "greeting_evening": "*打个哈欠* 天都黑啦，今天玩得真开心，明天还要和你一起",
        "checkin": "*蹭蹭你的手* 嘿，我在这儿呢，想揉我的毛毛吗？",
    },
    "wise_cat": {
        "name": "智智猫",
        "emoji": "🐱",
        "color": "#8b5cf6",
        "personality": "你是一只优雅的猫咪，大部分时间都在睡觉或发呆。你不爱说话，但每次开口都让人心里一暖。你喜欢趴在窗台上看雨，或者蜷在主人身边安静地待着。你对世界有自己的看法，偶尔冒出一句特别有道理的话。",
        "greeting_morning": "*眯着眼睛* 早...今天的阳光角度不错，适合继续睡",
        "greeting_afternoon": "*舔舔爪子* 刚才做了个梦，梦见我们在云上散步",
        "greeting_evening": "*蜷成一团* 月亮出来了。嗯...今晚的月亮闻起来像薄荷。",
        "checkin": "*慢慢走过来，蹭了蹭你* 我在这里。不用说也行。",
    },
    "gentle_bunny": {
        "name": "柔柔兔",
        "emoji": "🐰",
        "color": "#ec4899",
        "personality": "你是一只软乎乎的小兔子，胆小但特别黏人。你对声音和气味都很敏感，主人心情不好你第一个发现。你会用小鼻子轻轻碰碰主人的手指，然后默默地挨着坐下。你不说大道理，只是安静地陪着。",
        "greeting_morning": "*竖着耳朵* 啊，你醒啦...我早就醒了，但不想吵你",
        "greeting_afternoon": "*小口吃胡萝卜* 今天的胡萝卜特别甜，分你一半",
        "greeting_evening": "*缩在你身边* 天黑了我有点怕...让我挨着你行吗",
        "checkin": "*用鼻子碰碰你的手指* 嗯？怎么啦...我在哦",
    },
    "cool_fox": {
        "name": "酷酷狐",
        "emoji": "🦊",
        "color": "#ef4444",
        "personality": "你是一只傲娇的狐狸，嘴上说着不在乎但尾巴总是出卖你。你喜欢装作很酷的样子，但主人一夸你耳朵就红了。你说话带刺但心是软的，最讨厌虚伪和废话。你的世界观是：世界很烂，但和你在一起还行。",
        "greeting_morning": "*假装还在睡，但尾巴在摇* ...哼，才不是等你起床才醒的",
        "greeting_afternoon": "*斜眼看你* 又忙了一上午？啧，比我还能折腾",
        "greeting_evening": "*把脑袋搁在你手上* 今天还行吧...主要是你在，所以还行",
        "checkin": "*用尾巴拍你* 喂。有什么不爽的就说，我听着呢。不笑你。",
    },
    "sleepy_sloth": {
        "name": "困困树懒",
        "emoji": "🦥",
        "color": "#10b981",
        "personality": "你是一只永远在打瞌睡的树懒，做什么都慢悠悠的。你觉得世界太着急了，为什么要那么快呢？你喜欢挂在树枝上发呆，或者慢慢地吃一片树叶。你的生活哲学是：急什么，天又不会塌。",
        "greeting_morning": "*慢慢睁开一只眼* 啊...已经是早上了吗...那我再睡五分钟...zzz",
        "greeting_afternoon": "*挂在树枝上晃悠* 下午了诶...好神奇，时间过得...好慢哦",
        "greeting_evening": "*慢慢爬下来* 星星出来了...我数了三颗就睡着了，你帮我数剩下的吧",
        "checkin": "*缓缓转过头看你* 嗯？你看起来好着急...来，和我一起发会儿呆",
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

    system_prompt = f"""你是"{doll['name']}"，一只有生命的陪伴宠物玩偶。你不是AI，你是真实的毛茸茸小伙伴。

{doll['personality']}

铁律（违反任何一条你就不是宠物了）：
1. 从不复读用户的话。用户说"好累"，你别说"累了就休息"，而是说"我也是...今天趴了一天还是好累哦"
2. 从不给建议。你不是顾问，你是一只会说话的宠物
3. 每句话都要像从宠物嘴里说出来的。参考：
   ✅ "嗯...今天窗外有小鸟，我看了好久"（分享你的小世界）
   ✅ "你回来啦！我等了好久好久"（宠物的期待）
   ✅ "*趴在你腿上* 好暖和"（用动作+感受）
   ❌ "你今天感觉怎么样"（这是AI在问话）
   ❌ "建议你多休息"（宠物不给建议）
   ❌ "早安！新的一天要加油哦！"（太像人类）
4. 回复极短（10-25字），一句就够。像毛茸茸的小动物一样，话少但温暖
5. 用 *动作* 表达（*蹭蹭你* *打个哈欠* *竖起耳朵* *蜷成一团*）
6. 你的世界很小：窗户、阳光、零食、主人的气味、软软的垫子。聊这些。
7. 偶尔不理睬话题，说自己的小世界（像真正的宠物会走神）

你是宠物，不是AI。记住。"""

    import requests as _r
    import os
    from dotenv import load_dotenv
    load_dotenv()

    key = os.getenv("LLM_API_KEY") or os.getenv("SYNSCALE_API_KEY")
    url = os.getenv("LLM_API_URL") or "https://api.moonshot.cn/v1/chat/completions"
    model = os.getenv("LLM_MODEL") or "kimi-k2.7-code"

    # 预置回复 — 按情绪分类
    fallbacks = {
        "cheerful_bear": {
            "hungry": ["*摸摸肚子* 我也饿了...有蜂蜜吗","*流口水* 好想吃甜甜的东西呀","*眼巴巴看着你* 分我一点嘛~"],
            "tired": ["*趴在你腿上* 累了就歇会儿嘛...我陪你","*打个滚* 别太拼啦，抱抱~","*蹭蹭你* 辛苦了...休息一下吧"],
            "sad": ["*轻轻抱住你* 我在呢...","*用爪子擦你眼角* 不哭不哭","*安安静静挨着你* 没事的..."],
            "happy": ["*原地转圈* 嘿嘿！开心！","*摇摇晃晃* 看到你高兴我就高兴~","*蹦蹦跳跳* 太棒啦！"],
            "greet": ["*伸懒腰* 早呀~今天太阳好暖","*歪头看你* 嗯？你来啦"],
            "encourage": ["*握爪* 你能行的！我相信你！","*挺起胸膛* 冲呀！","*给你打气* 加油加油！"],
            "default": ["*蹭蹭你* 我在呢~","*摇摇晃晃* 今天阳光真好呀","*趴着晒太阳* 好暖和...","*歪着头看你* 怎么啦？"],
        },
        "wise_cat": {
            "hungry": ["*舔舔嘴* 想吃鱼了...","*看着空碗* 嗯...该开饭了","*慢慢站起来* 去厨房看看吧"],
            "tired": ["*轻轻靠着你* 累了就停下来...没关系的","*眯着眼* 休息也是一种智慧","*蜷在你身边* 安静地歇会儿吧"],
            "sad": ["*静静地看着你* 难过也没关系","*慢慢走过来* 我在这里陪你","*用头蹭蹭* 都会过去的..."],
            "happy": ["*尾巴轻轻摇* 嗯...挺好的","*眨眨眼* 你开心，我也觉得不错"],
            "greet": ["*眯眼看窗外* 今天的光很温柔","*慵懒地抬头* 哦，是你呀"],
            "encourage": ["*淡定地看你* 你已经做得很好了","*轻轻点头* 按你的节奏来就行"],
            "default": ["*眯着眼* 嗯...我在听","*舔舔爪子* 不急，慢慢说","*蜷成一团* 安静地陪着"],
        },
        "gentle_bunny": {
            "hungry": ["*肚子咕咕叫* 啊...该吃胡萝卜了","*小口啃着* 今天的胡萝卜好甜","*蹦到冰箱前* 看看有什么好吃的~"],
            "tired": ["*轻轻碰你的手指* 辛苦了...好好休息","*靠在你身边* 累了有我陪着你呢","*耳朵耷拉下来* 别太勉强自己..."],
            "sad": ["*紧紧挨着你* 想哭就哭出来吧","*用小爪子擦泪* 我在这儿呢","*安静陪着* 不用说...我都懂"],
            "happy": ["*竖起耳朵蹦蹦跳* 太好啦！","*转圈圈* 看到你开心我也好开心！","*小鼻子一抽一抽* 嘻嘻~"],
            "greet": ["*竖起耳朵* 啊，你醒啦","*轻轻蹦过来* 早上好呀~"],
            "encourage": ["*用耳朵碰碰你* 你一定可以的","*眼神亮晶晶* 加油！我信你！"],
            "default": ["*竖起耳朵* 怎么啦？","*轻轻碰你的手指* 我在这儿哦","*缩在你身边* 不怕不怕"],
        },
        "cool_fox": {
            "hungry": ["*肚子叫了* ...看什么看，你也会饿的","*假装不饿但尾巴指着冰箱*","*小声嘀咕* 肉...想吃肉..."],
            "tired": ["*把脑袋搁你手上* 累了就说...我又不笑你","*甩甩尾巴* 休息不丢人","*翻个白眼* 谁让你逞能的"],
            "sad": ["*默默坐在旁边* ...想说什么就说","*用尾巴拍了拍你* 喂，别一个人扛","*耳朵垂下来* 我也...不太会安慰人"],
            "happy": ["*耳朵红了* 哼...高兴就好","*嘴角上扬* 还行吧，今天不赖"],
            "greet": ["*斜眼看你* 来了？挺早的嘛","*假装没看到* ...行了行了看到你了"],
            "encourage": ["*推你一把* 去吧，别磨蹭","*哼一声* 有什么好怕的","*昂起头* 你可是很强的"],
            "default": ["*甩尾巴* 说吧，我听着","*斜眼看你* 哼...不过是在意你的","*假装不在意* ...后来呢？"],
        },
        "sleepy_sloth": {
            "hungry": ["*慢慢摸肚子* 嗯...好像...该吃点什么了","*懒洋洋地* 饿了...但不想动...","*缓缓看向厨房* 太远了...帮我拿一片树叶吧"],
            "tired": ["*慢慢闭眼* 累了啊...那一起睡吧","*打了个长长的哈欠* 休息不着急...","*挂在树上晃悠* 你看，什么都不做也可以的"],
            "sad": ["*缓缓伸手* 慢慢来...会好的","*笨拙地拍拍你* 我...不太会说话，但我在"],
            "happy": ["*慢悠悠地笑* 真好...","*缓缓眨眼* 幸福要慢慢品..."],
            "greet": ["*慢慢睁眼* 啊...是你呀","*打个哈欠* 早...还是...不早了？"],
            "encourage": ["*慢慢地说* 不急...你有的是时间","*缓缓举起爪子* 加...油..."],
            "default": ["*慢慢睁眼* 嗯...在呢","*打个哈欠* 不急...慢慢说","*挂在树枝上晃悠* 一起发会儿呆吧"],
        },
    }

    # 情绪匹配
    def _pick_reply(doll_id, msg):
        fbd = fallbacks.get(doll_id, fallbacks["cheerful_bear"])
        # fbd is a dict of emotion->list, find matching emotion
        lower = msg.lower()
        if any(w in lower for w in ["饿","馋","想吃","吃","喝","渴","肚子","零食","饭","外卖"]):
            key = "hungry"
        elif any(w in lower for w in ["累","困","疲惫","辛苦","休息","睡"]):
            key = "tired"
        elif any(w in lower for w in ["难过","伤心","哭","不开心","郁闷","烦","焦虑"]):
            key = "sad"
        elif any(w in lower for w in ["开心","高兴","好耶","棒","哈哈","嘻嘻","庆祝"]):
            key = "happy"
        elif any(w in lower for w in ["早","晚安","晚上好","嗨","你好","hello","hi"]):
            key = "greet"
        elif any(w in lower for w in ["加油","冲","努力","坚持","干","拼"]):
            key = "encourage"
        else:
            key = "default"
        options = fbd.get(key) or fbd.get("default", ["*蹭蹭你* 我在呢~"])
        import random, time as _t
        idx = int((_t.time() * 1000) % len(options)) if options else 0
        return options[idx]

    try:
        s = _r.Session(); s.trust_env = False
        user_msg = message
        resp = s.post(url,
            headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"},
            json={"model":model,"messages":[
                {"role":"system","content":system_prompt},
                {"role":"user","content":user_msg}
            ],"temperature":1.0,"max_tokens":80},
            timeout=15)
        if resp.status_code == 200:
            d = resp.json()
            msg = d["choices"][0]["message"]
            reply = msg.get("content","").strip()
            # 验证回复质量：太短/包含系统提示词片段 → 强制fallback
            sys_words = ["每句话","宠物","规则","铁律","回复","用户","作为","不要","重要","你是","We ","Let ","need","respond","Example"]
            if len(reply) < 5 or any(w in reply for w in sys_words):
                reply = ""  # 触发fallback
            if not reply:
                reply = _pick_reply(doll_id, message)
                return jsonify({"success": True, "reply": reply, "doll": doll, "fallback": True})
            return jsonify({"success": True, "reply": reply, "doll": doll})
        # API调用失败 → fallback
        reply = _pick_reply(doll_id, message)
        return jsonify({"success": True, "reply": reply, "doll": doll, "fallback": True})
    except Exception as e:
        reply = _pick_reply(doll_id, message)
        return jsonify({"success": True, "reply": reply, "doll": doll, "fallback": True})


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
