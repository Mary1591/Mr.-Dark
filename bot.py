import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
INDEX_FILE = "books.json"
ID_GRUP_MARE = 1957960999  

# O cheie secretă aleasă de tine ca să nu poată altcineva să îți modifice lista
SECRET_KEY = "maria_secret_key_2026" 

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text("Te rog scrie: /cauta [titlu sau autor]")
        return

    query = " ".join(context.args).lower()
    index = load_index()
    results = [name for name in index if query in name.lower()]
    
    if results:
        text = "📚 *Cărți găsite în bibliotecă:*\n\n"
        for name in results[:5]:  
            link = f"https://t.me/c/{ID_GRUP_MARE}/{index[name]}"
            text += f"• [{name}]({link})\n"
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await update.message.reply_text("❌ Nu am găsit nicio carte cu acest titlu în bibliotecă.")

# Comanda secretă prin care calculatorul tău va urca fișierul JSON direct în bot
async def update_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.document:
        return
    
    # Verificăm dacă cel care trimite a pus cheia secretă în descriere
    if context.args and context.args[0] == SECRET_KEY:
        file = await context.message.document.get_file()
        await file.download_to_drive(INDEX_FILE)
        await update.message.reply_text("✅ Baza de date a fost actualizată cu succes în privat!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("cauta", search))
app.add_handler(CommandHandler("update_books", update_db))

if __name__ == "__main__":
    app.run_polling()
