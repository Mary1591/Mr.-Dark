import json
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
INDEX_FILE = "books.json"

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_index(index):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

# Funcție secundară care rulează în fundal pentru a șterge mesajul după 3 minute
async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception:
        pass  # Dacă mesajul a fost deja șters manual, ignoră eroarea

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.document:
        return

    doc = update.message.document
    if not doc.file_name.lower().endswith((".epub", ".pdf")):
        return

    index = load_index()
    name = doc.file_name
    chat_id = update.message.chat_id
    msg_id = update.message.message_id

    if name in index:
        # Ștergem fișierul duplicat trimis de membru (necesită ca botul să fie Admin)
        try:
            await update.message.delete()
        except Exception:
            pass 

        # Generăm link-ul către postarea originală
        # Eliminăm -100 din ID-ul chat-ului de supergrup pentru link-urile t.me/c/
        clean_chat_id = str(chat_id).replace("-100", "")
        original_link = f"https://t.me/c/{clean_chat_id}/{index[name]}"
        
        warning = await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ *DUPLICAT DETECTAT*\n\nFișierul `{name}` există deja.\n"
                 f"👉 Îl poți găsi aici: {original_link}\n\n_(Acest mesaj va fi șters în 3 minute)_",
            parse_mode="Markdown"
        )
        
        # Programăm ștergerea mesajului de avertizare peste 180 de secunde (fără a bloca botul)
        context.job_queue.run_once(delete_message_job, 180, chat_id=chat_id, data=warning.message_id)
    else:
        index[name] = msg_id
        save_index(index)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    if not context.args:
        await update.message.reply_text("Te rog scrie: /search [titlu]")
        return

    query = " ".join(context.args).lower()
    index = load_index()
    chat_id = update.message.chat_id
    
    results = [name for name in index if query in name.lower()]
    
    if results:
        clean_chat_id = str(chat_id).replace("-100", "")
        text = "📚 *Găsite:*\n"
        for name in results[:5]:  # Afișează primele 5 rezultate
            link = f"https://t.me/c/{clean_chat_id}/{index[name]}"
            text += f"• [{name}]({link})\n"
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await update.message.reply_text("❌ Nu am găsit nicio carte cu acel titlu.")

# Inițializare aplicație cu suport pentru JobQueue (necesar pentru ștergerea programată)
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("search", search))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

# Pornire bot
app.run_polling()
