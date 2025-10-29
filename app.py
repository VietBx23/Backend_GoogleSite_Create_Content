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
import json, re, time, os

# ========================================
# ⚙️ 读取 API Key（从环境变量中获取）
# ========================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ 缺少 OPENAI_API_KEY 环境变量，请在 Render 上设置 Environment Variables。")

# ✅ 使用 OpenRouter 代理（可换成官方 endpoint）
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
        f"3. 确保主关键词 \"{main_kw}\" 在内容中出现 3-5 次；\n"
        "4. 内容流畅自然，长度 150~200 字；\n"
        "5. 不要换行，不要添加解释。"
    )
    text = call_chat(prompt, max_tokens=500, temperature=0.7)  # Tăng max_tokens để đảm bảo độ dài
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
    # Render 要求 app 监听在 PORT 环境变量上
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
