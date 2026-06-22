import json, os, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
INDEX_FILE = "books.json"

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE) as f:
            return json.load(f)
    return {}

def save_index(index):
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.lower().endswith((".epub", ".pdf")):
        return
    index = load_index()
    name = doc.file_name
    chat_id = update.message.chat_id
    msg_id = update.message.message_id
    if name in index:
        original_link = f"https://t.me/c/{str(chat_id)[4:]}/{index[name]}"
        warning = await update.message.reply_text(
            f"⚠️ *DUPLICAT DETECTAT*\n\nFișierul `{name}` există deja.\n"
            f"👉 Îl poți găsi aici: {original_link}\n\n_(Acest mesaj va fi șters în 3 minute)_",
            parse_mode="Markdown"
        )
        await asyncio.sleep(180)
        await warning.delete()
    else:
        index[name] = msg_id
        save_index(index)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Te rog scrie: /search [titlu]")
        return
    query = " ".join(context.args).lower()
    index = load_index()
    chat_id = update.message.chat_id
    results = [name for name in index if query in name.lower()]
    if results:
        text = "📚 *Găsite:*\n"
        for name in results[:5]:
            link = f"https://t.me/c/{str(chat_id)[4:]}/{index[name]}"
            text += f"• [{name}]({link})\n"
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Nu am găsit nicio carte cu acel titlu.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("search", search))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.run_polling()
