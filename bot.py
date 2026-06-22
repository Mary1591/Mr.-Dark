import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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

# Funcția CAUTA revizuită: generează link-uri albastre către mesaje, exact cum era la început
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    if not context.args:
        await update.message.reply_text("Te rog scrie: /cauta [titlu sau autor]")
        return

    query = " ".join(context.args).lower()
    index = load_index()
    chat_id = update.message.chat_id
    
    # Căutăm toate cărțile care conțin textul căutat
    results = [name for name in index if query in name.lower()]
    
    if results:
        # Curățăm ID-ul chat-ului pentru a genera link-uri interne corecte de tip t.me/c/
        clean_chat_id = str(chat_id).replace("-100", "")
        text = "📚 *Cărți găsite în bibliotecă:*\n\n"
        
        for name in results[:5]:  # Afișează primele 5 rezultate găsite
            link = f"https://t.me/c/{clean_chat_id}/{index[name]}"
            text += f"• [{name}]({link})\n"
            
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await update.message.reply_text("❌ Nu am găsit nicio carte cu acel titlu în bibliotecă.")

# Inițializare aplicație în modul clasic și curat
app = ApplicationBuilder().token(TOKEN).build()

# Înregistrare comandă
app.add_handler(CommandHandler("cauta", search))

# Pornire bot
if __name__ == "__main__":
    app.run_polling()
