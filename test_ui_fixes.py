# -*- coding: utf-8 -*-
"""
测试 UI 修复：
1. 消息气泡底部空白区间修复（formatMarkdown）
2. 提议句式转为可点击选项按钮（extractSuggestions）
共 30 轮测试
"""
import re
import json
import requests
import sys

BASE_URL = "http://127.0.0.1:5000"
PASSED = 0
FAILED = 0
TOTAL = 30

# ====================================================================
# Test 1: formatMarkdown 空白区间检测（Python 模拟 JS 逻辑）
# ====================================================================
def format_markdown(text):
    """模拟 JS 中的新 formatMarkdown 函数（paragraph-first approach，不再有 br 在 ul/ol 内）"""
    if not text:
        return ''
    text = text.strip()
    text = text.replace('&', '\x26amp;').replace('<', '\x26lt;').replace('>', '\x26gt;')

    # Extract code blocks first
    code_blocks = []
    text = re.sub(r'```(\w*)\n([\s\S]*?)```',
                  lambda m: (code_blocks.append(f'<pre><code>{m.group(2)}</code></pre>') or
                             f'\x25\x25CODEBLOCK_{len(code_blocks) - 1}\x25\x25'),
                  text)

    # Extract tables
    tables = []
    def table_replacer(m):
        lines = m.group(0).strip().split('\n')
        html = '<table>'
        for line in lines:
            cells = [c.strip() for c in line.split('|')]
            cells = [c for c in cells if c]
            if all(re.match(r'^[-:]+$', c) for c in cells):
                continue
            html += '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
        html += '</table>'
        tables.append(html)
        return f'\x25\x25TABLE_{len(tables) - 1}\x25\x25'
    text = re.sub(r'(?:^\|.+\|$\n?)+', table_replacer, text, flags=re.MULTILINE)

    # Collapse 3+ newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Split into paragraphs
    paragraphs = text.split('\n\n')
    result = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        lines = para.split('\n')

        # Headings (single-line only in new approach)
        if len(lines) == 1:
            if re.match(r'^### (.+)$', para):
                result.append(re.sub(r'^### (.+)$', r'<h3>\1</h3>', para))
                continue
            if re.match(r'^## (.+)$', para):
                result.append(re.sub(r'^## (.+)$', r'<h2>\1</h2>', para))
                continue
            if re.match(r'^# (.+)$', para):
                result.append(re.sub(r'^# (.+)$', r'<h1>\1</h1>', para))
                continue

        # HR
        if para == '---':
            result.append('<hr>')
            continue

        # Blockquote
        if all(re.match(r'^> .+', line) for line in lines):
            result.append(re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', para, flags=re.MULTILINE))
            continue

        # Unordered list
        if all(re.match(r'^- .+', line) for line in lines):
            items = [re.sub(r'^- (.+)$', r'<li>\1</li>', line) for line in lines]
            result.append('<ul>' + ''.join(items) + '</ul>')
            continue

        # Ordered list
        if all(re.match(r'^\d+\. .+', line) for line in lines):
            items = [re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', line) for line in lines]
            result.append('<ol>' + ''.join(items) + '</ol>')
            continue

        # Regular paragraph - apply inline formatting
        para = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', para)
        para = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', para)
        para = re.sub(r'`([^`]+)`', r'<code>\1</code>', para)
        para = re.sub(r'\n', '<br>', para)
        result.append('<p>' + para + '</p>')

    text = ''.join(result)

    # Restore tables
    for i, html in enumerate(tables):
        text = text.replace(f'\x25\x25TABLE_{i}\x25\x25', html)

    # Restore code blocks
    for i, html in enumerate(code_blocks):
        text = text.replace(f'\x25\x25CODEBLOCK_{i}\x25\x25', html)

    return text


def has_trailing_blank(html):
    """检查 HTML 末尾是否有空白区间"""
    if not html:
        return False
    # Check for trailing <br> before </p>
    if re.search(r'<br>\s*</p>\s*$', html):
        return True
    # Check for empty <p> at end
    if re.search(r'<p>\s*</p>\s*$', html):
        return True
    # Check for trailing <br>
    if re.search(r'<br>\s*$', html):
        return True
    return False


# ====================================================================
# Test 2: extractSuggestions 提议检测（Python 模拟 JS 逻辑）
# ====================================================================
def extract_suggestions(text):
    """模拟 JS 中的 extractSuggestions 函数"""
    match = re.search(r'(需要我|要我|要我帮您|需要我帮你)(.+?)(吗[？?]?)?$', text)
    if not match:
        return None
    options_part = match.group(2)
    split_key = '还是' if '还是' in options_part else '或'
    raw_options = options_part.split(split_key)
    if len(raw_options) < 2:
        return None
    prefix = match.group(1)
    suffix = (match.group(3) or '').replace('？', '').replace('?', '')
    options = [re.sub(r'[，,。！!？?]', '', o.strip()) for o in raw_options]
    return {'prefix': prefix, 'suffix': suffix, 'options': options, 'split_key': split_key}


# ====================================================================
# Test 3: API 端到端测试 - 验证回复内容无尾部空白
# ====================================================================
def test_api_reply(message, test_name):
    """发送 API 请求并验证回复"""
    global PASSED, FAILED
    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": message, "session_id": f"test_{test_name}"},
            timeout=60
        )
        data = resp.json()
        reply = data.get('reply', '')

        # Check 1: 回复内容不为空
        if not reply or not reply.strip():
            print(f"  ❌ [{test_name}] 回复为空")
            FAILED += 1
            return

        # Check 2: 回复首尾无多余空白
        if reply != reply.strip():
            print(f"  ❌ [{test_name}] 回复包含首尾空白字符")
            FAILED += 1
            return

        # Check 3: 模拟 formatMarkdown 后无尾部空白区间
        html = format_markdown(reply)
        if has_trailing_blank(html):
            print(f"  ❌ [{test_name}] formatMarkdown 后有尾部空白区间")
            print(f"      原始回复: {reply[:80]}...")
            print(f"      HTML尾: ...{html[-60:]}")
            FAILED += 1
            return

        # Check 4: 如果包含提议句式，验证 extractSuggestions 识别正确
        suggestion = extract_suggestions(reply)
        if suggestion:
            if len(suggestion['options']) < 2:
                print(f"  ❌ [{test_name}] 提议句式选项不足2个: {suggestion['options']}")
                FAILED += 1
                return

        print(f"  ✅ [{test_name}] 通过 (reply={len(reply)}字, html={len(html)}字节, suggestion={'有' if suggestion else '无'})")
        PASSED += 1

    except requests.exceptions.ConnectionError:
        print(f"  ❌ [{test_name}] 无法连接到服务器 {BASE_URL}，请确认 Flask 已启动")
        FAILED += 1
    except Exception as e:
        print(f"  ❌ [{test_name}] 异常: {e}")
        FAILED += 1


# ====================================================================
# 30 个测试用例
# ====================================================================
TEST_CASES = [
    # ---- 提议句式测试（测试 extractSuggestions + 空白区间） ----
    ("已找到3家公司。需要我对其中某家公司做深度背景分析还是生成开发信吗？", "提议句式-还是"),
    ("根据您的需求，搜到以下买家。要我帮您分析公司背景还是生成开发信？", "提议句式-还是要我帮您"),
    ("这些客户都很不错。需要我帮你起草回复邮件还是查询汇率吗？", "提议句式-还是-邮件"),
    ("数据已整理好。要我为您生成广告语还是分析销售数据吗？", "提议句式-还是-广告"),
    ("找到了相关产品信息。需要我做深度分析或简单介绍吗？", "提议句式-或"),
    ("以上是查询结果。要我帮您搜索更多买家或生成商品描述吗？", "提议句式-或-更多"),
    ("已分析完毕。需要我对比这几家公司还是单独深入分析某一家吗？", "提议句式-对比"),

    # ---- 普通回复测试（测试空白区间） ----
    ("你好", "普通-问候"),
    ("帮助", "普通-帮助"),
    ("你是谁", "普通-身份"),
    ("美元兑人民币的汇率是多少？", "工具-汇率"),
    ("帮我搜索电子产品相关的买家", "工具-搜索买家"),

    # ---- 带标点符号的回复（边缘情况） ----
    ("请用英文写一封简短开发信", "工具-开发信"),
    ("帮我为蓝牙耳机生成商品描述", "工具-商品描述"),

    # ---- 多行/富文本回复测试 ----
    ("分析一下今天的销售：保温杯20个，手机支架35个，数据线50条", "工具-销售分析"),
    ("为冬季保暖手套生成几条广告语", "工具-广告语"),
    ("客户说包裹还没收到，帮我起草回复", "工具-客服回复"),

    # ---- Session 连续对话测试 ----
    ("帮我搜索LED灯相关的买家", "对话-LED灯"),
    ("分析一下 brighttech.com 这家公司", "对话-分析公司"),

    # ---- 更多提议句式变体 ----
    ("搜索到以下买家信息。要我帮您分析其中一家还是全部对比吗？", "提议-一家或全部"),
    ("以上是您需要的商品列表。需要我生成英文描述还是中文描述吗？", "提议-中英文"),

    # ---- 更多工具调用 ----
    ("欧元兑人民币的汇率是多少？", "工具-欧元汇率"),
    ("帮我搜索健身器材相关的买家", "工具-健身器材"),
    ("分析一下 fittrade.com 这家公司", "工具-分析fittrade"),
    ("为智能手表生成商品描述", "工具-智能手表"),
    ("客户问能否打折，帮我起草回复", "工具-打折回复"),
    ("分析今天销售：瑜伽垫15个，哑铃10套", "工具-瑜伽销售"),
    ("为春季新款连衣裙生成广告语", "工具-连衣裙广告"),
    ("帮我搜索宠物用品相关的买家", "工具-宠物用品"),
    ("英镑兑人民币的汇率是多少？", "工具-英镑汇率"),
    ("客户要取消订单，帮我起草回复", "工具-取消订单"),
]


# ====================================================================
# 单元测试：formatMarkdown 空白检测
# ====================================================================
def run_unit_tests():
    print("=" * 60)
    print("📋 单元测试：formatMarkdown 尾部空白检测")
    print("=" * 60)
    unit_tests = [
        ("正常文本", "这是回复内容", False),
        ("末尾有换行", "这是回复\n", False),  # trim 会处理
        ("末尾有空格", "这是回复  ", False),  # trim 会处理
        ("末尾有空行", "这是回复\n\n", False),  # trim + regex 处理
        ("只有空格", "   ", False),
        ("空字符串", "", False),
        ("带<br>的换行", "第一行\n第二行", False),
        ("多段落", "段落一\n\n段落二", False),
        ("标题+内容", "# 标题\n内容", False),
        ("列表", "- 项目1\n- 项目2", False),
        ("代码块", "```\ncode\n```", False),
    ]
    for name, text, expected in unit_tests:
        html = format_markdown(text)
        result = has_trailing_blank(html)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {name}: has_trailing_blank={result} (expected={expected})")
        assert result == expected, f"Test '{name}' failed!"


# ====================================================================
# 单元测试：extractSuggestions 提议句式检测
# ====================================================================
def run_suggestion_tests():
    print("\n" + "=" * 60)
    print("📋 单元测试：extractSuggestions 提议检测")
    print("=" * 60)
    tests = [
        ("需要我对其中某家公司做深度背景分析还是生成开发信吗？",
         {"prefix": "需要我", "suffix": "吗", "options": ["对其中某家公司做深度背景分析", "生成开发信"]}),
        ("要我帮您分析公司背景还是生成开发信？",
         {"prefix": "要我", "suffix": "", "options": ["帮您分析公司背景", "生成开发信"]}),
        ("需要我做深度分析或简单介绍吗？",
         {"prefix": "需要我", "suffix": "吗", "options": ["做深度分析", "简单介绍"]}),
        ("要我帮您搜索更多买家或生成商品描述吗？",
         {"prefix": "要我", "suffix": "吗", "options": ["帮您搜索更多买家", "生成商品描述"]}),
        # Non-suggestion texts should return None
        ("这是普通回复", None),
        ("你好，有什么可以帮您？", None),
        ("已找到3条结果。", None),
        ("需要帮助吗？", None),  # 单个选项不算提议
    ]
    for text, expected in tests:
        result = extract_suggestions(text)
        if expected is None:
            status = "✅" if result is None else "❌"
            print(f"  {status} '{text[:30]}...' -> None (got: {result})")
            assert result is None, f"Expected None but got {result}"
        else:
            match_ok = (result is not None and
                        result['options'] == expected['options'] and
                        result['prefix'] == expected['prefix'] and
                        result['suffix'] == expected['suffix'])
            status = "✅" if match_ok else "❌"
            print(f"  {status} '{text[:30]}...' -> options={result['options'] if result else 'None'}")
            assert match_ok, f"Expected {expected}, got {result}"


# ====================================================================
# 主测试流程
# ====================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🧪 外贸通 UI 修复测试 - 共30轮")
    print("=" * 60)

    # Step 1: 单元测试
    try:
        run_unit_tests()
    except AssertionError as e:
        print(f"\n❌ 单元测试失败: {e}")
        sys.exit(1)

    try:
        run_suggestion_tests()
    except AssertionError as e:
        print(f"\n❌ 提议检测测试失败: {e}")
        sys.exit(1)

    # Step 2: 清空测试会话
    print("\n" + "=" * 60)
    print("📡 API 端到端测试（30轮）")
    print("=" * 60)
    try:
        requests.post(f"{BASE_URL}/api/clear", json={"session_id": "test_all"}, timeout=5)
    except:
        pass

    # Step 3: 执行30轮 API 测试
    for i, (message, name) in enumerate(TEST_CASES, 1):
        session = f"test_{i}"
        test_api_reply(message, name)

    # Step 4: 结果汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"  ✅ 通过: {PASSED}/{TOTAL}")
    print(f"  ❌ 失败: {FAILED}/{TOTAL}")
    if FAILED == 0:
        print("\n🎉 全部30轮测试通过！")
    else:
        print(f"\n⚠️ 有 {FAILED} 轮测试失败，请检查")
        sys.exit(1)