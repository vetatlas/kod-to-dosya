import os, io, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 8080))
gecici = {}

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *a): pass

def run_http():
    HTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()

async def start(update, context):
    await update.message.reply_text(
        "📄 <b>Kod → Dosya Botu</b>\n\n"
        "Bana bir kod yapıştır, ben onu dosya olarak geri gönderirim.\n\n"
        "👇 Hemen bir kod mesajı gönder.",
        parse_mode=ParseMode.HTML
    )

async def kod_al(update, context):
    uid = update.message.from_user.id
    metin = update.message.text or update.message.caption or ""
    if not metin.strip():
        await update.message.reply_text("⚠️ Boş mesaj.")
        return
    gecici[uid] = metin
    klavye = [
        [InlineKeyboardButton("🐍 Python (.py)", callback_data="fmt_py"),
         InlineKeyboardButton("📝 Metin (.txt)", callback_data="fmt_txt")],
        [InlineKeyboardButton("📜 JavaScript (.js)", callback_data="fmt_js"),
         InlineKeyboardButton("📦 JSON (.json)", callback_data="fmt_json")],
        [InlineKeyboardButton("🌐 HTML (.html)", callback_data="fmt_html"),
         InlineKeyboardButton("🎨 CSS (.css)", callback_data="fmt_css")],
        [InlineKeyboardButton("⚙️ YAML (.yaml)", callback_data="fmt_yaml"),
         InlineKeyboardButton("🐚 Shell (.sh)", callback_data="fmt_sh")],
        [InlineKeyboardButton("❌ İptal", callback_data="fmt_iptal")],
    ]
    await update.message.reply_text(
        f"📄 <b>Kod alındı</b> ({len(metin)} karakter)\n\n"
        f"Hangi formatta gönderelim?",
        reply_markup=InlineKeyboardMarkup(klavye),
        parse_mode=ParseMode.HTML
    )

async def format_secildi(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    if data == "fmt_iptal":
        gecici.pop(uid, None)
        await q.edit_message_text("❌ İptal edildi.")
        return

    kod = gecici.pop(uid, None)
    if not kod:
        await q.edit_message_text("⚠️ Kod kaybolmuş. Yeni bir kod gönder.")
        return

    uzanti = data.replace("fmt_", "")
    dosya = io.BytesIO(kod.encode("utf-8"))
    dosya.name = f"kod.{uzanti}"

    await q.edit_message_text(
        f"✅ <b>kod.{uzanti}</b> hazırlanıyor...",
        parse_mode=ParseMode.HTML
    )

    await context.bot.send_document(
        chat_id=q.message.chat_id,
        document=dosya,
        filename=f"kod.{uzanti}",
        caption=f"📄 <b>kod.{uzanti}</b>\n📏 {len(kod)} karakter",
        parse_mode=ParseMode.HTML
    )

def main():
    threading.Thread(target=run_http, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(format_secildi, pattern="^fmt_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, kod_al))
    app.run_polling()

if __name__ == "__main__":
    main()
