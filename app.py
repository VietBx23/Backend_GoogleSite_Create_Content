# 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
# filename: app.py
"""
🔥 多关键词生成后端（Flask + OpenAI API）
-----------------------------------------
✅ 接收前端 POST JSON：
   {
       "keywords": "线上赌博app\nPG电子平台\n在线澳门赌博\n正规赌博平台\n正规赌博",
       "url": "http://191.run"
   }

✅ 返回 JSON：
   [
       {
           "main": "线上赌博app",
           "related": ["词1","词2","词3","词4","词5"],
           "bing_url": "https://www.bing.com/search?q=线上赌博app，词1，词2...",
           "content": "线上赌博app【网址：http://191.run】......"
       },
       ...
   ]
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json, re, time

# ========================================
# ⚙️ API Key（请在此粘贴你的 API Key）
# ========================================
OPENAI_API_KEY = "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"  # ← ⚠️ 记得替换
client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://openrouter.ai/api/v1")
MODEL = "gpt-4o-mini"

# 初始化 Flask
app = Flask(__name__)
CORS(app)

# ========================================
# 🔧 工具函数
# ========================================
def call_chat(prompt, max_tokens=300, temperature=0.6):
    """调用 OpenAI 聊天模型"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()


def generate_related_keywords(main_kw):
    """生成 5 个相关关键词"""
    prompt = (
        f"请为关键词：\"{main_kw}\" 生成5个相关的中文长尾关键词。\n"
        "要求：与主题高度相关，每个约5~8字。\n"
        "只输出JSON数组格式，例如: [\"词1\",\"词2\",...]\n"
        "不要添加任何多余说明。"
    )
    text = call_chat(prompt)
    try:
        arr = json.loads(text)
        if isinstance(arr, list):
            return [s.strip() for s in arr][:5]
    except Exception:
        parts = re.split(r"[,\n;，；\s]+", text)
        return [p.strip() for p in parts if p.strip()][:5]
    return []


def generate_content(main_kw, related_kws, url="http://191.run"):
    """生成描述内容"""
    related_str = "，".join(related_kws)
    prompt = (
        f"请为主关键词 \"{main_kw}\" 写一段中文介绍：\n"
        f"1. 必须以：{main_kw}【网址：{url}】开头；\n"
        f"2. 在后续描述中自然融入 3~5 个以下关键词：{related_str}；\n"
        "3. 内容流畅自然，长度 120~180 字；\n"
        "4. 不要换行，不要添加解释。"
    )
    text = call_chat(prompt, max_tokens=400, temperature=0.7)
    return " ".join(text.split())


# ========================================
# 🔥 API 路由
# ========================================
@app.route("/generate", methods=["POST"])
def generate():
    """接收前端 JSON 并返回生成结果"""
    data = request.get_json()
    if not data or "keywords" not in data:
        return jsonify({"error": "缺少关键词"}), 400

    raw_keywords = data["keywords"].strip()
    url = data.get("url", "http://191.run").strip()

    # 按行分割关键词
    main_keywords = [kw.strip() for kw in raw_keywords.splitlines() if kw.strip()]
    if not main_keywords:
        return jsonify({"error": "关键词不能为空"}), 400

    results = []

    for kw in main_keywords:
        try:
            related = generate_related_keywords(kw)
            content = generate_content(kw, related, url)
            keyword_line = "，".join([kw] + related)
            bing_url = f"https://www.bing.com/search?q={keyword_line}"

            results.append({
                "main": kw,
                "related": related,
                "bing_url": bing_url,
                "content": content
            })

            time.sleep(0.5)

        except Exception as e:
            results.append({
                "main": kw,
                "error": str(e)
            })

    return jsonify(results)


@app.route("/")
def home():
    return "✅ Backend API 已启动，可通过 POST /generate 生成内容。"


# ========================================
# 🚀 启动
# ========================================
if __name__ == "__main__":
    app.run(debug=True)
