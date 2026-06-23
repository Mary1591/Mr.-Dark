import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
INDEX_FILE = "books.json"

# ID-ul grupului tău CEL MARE (îl vom schimba când îl aflăm, momentan lăsăm 0)
ID_GRUP_MARE = 1957960999  

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
            # Link-ul va trimite fetele direct pe grupul cel mare la mesajul potrivit
            link = f"https://t.me/c/{ID_GRUP_MARE}/{index[name]}"
            text += f"• [{name}]({link})\n"
            
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await update.message.reply_text("❌ Nu am găsit nicio carte cu acest titlu în bibliotecă.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("cauta", search))

if __name__ == "__main__":
    app.run_polling()
