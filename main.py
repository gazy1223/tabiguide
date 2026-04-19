import os
import json
import base64
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

PROMPT = """
この写真に写っている建物や場所を分析して、以下のJSON形式で回答してください。

{
  "place": "場所・建物の名前",
  "location": "国・地域・都市",
  "ja": {
    "overview": "概要を2〜3文で",
    "history": "歴史的背景を2〜3文で",
    "culture": "文化・見どころを2〜3文で"
  },
  "fr": {
    "overview": "Aperçu en 2-3 phrases",
    "history": "Histoire en 2-3 phrases",
    "culture": "Culture et points d'intérêt en 2-3 phrases"
  },
  "tags": ["タグ1", "タグ2", "タグ3"]
}

JSONのみを返してください。前後に説明文は不要です。
"""

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 写真を受け取りました。分析中です...")

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{
            "parts": [
                {"text": PROMPT},
                {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}
            ]
        }],
        "generationConfig": {"temperature": 0.4}
    }

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(url, json=payload)
        data = res.json()

    raw = data["candidates"][0]["content"]["parts"][0]["text"]
    raw = raw.replace("```json", "").replace("```", "").strip()
    info = json.loads(raw)

    msg = f"""
🗺 *{info['place']}*
📍 {info['location']}

🇯🇵 *日本語ガイド*

📖 *概要*
{info['ja']['overview']}

🏛 *歴史*
{info['ja']['history']}

✨ *文化・見どころ*
{info['ja']['culture']}

━━━━━━━━━━━━━━

🇫🇷 *Guide en français*

📖 *Aperçu*
{info['fr']['overview']}

🏛 *Histoire*
{info['fr']['history']}

✨ *Culture*
{info['fr']['culture']}

━━━━━━━━━━━━━━
🏷 {" · ".join(info['tags'])}
"""

    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 建物や場所の写真を送ってください！\n日本語とフランス語でガイドします。"
    )


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT, handle_text))

if __name__ == "__main__":
    print("ボット起動中...")
    app.run_polling()
