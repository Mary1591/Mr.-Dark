import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
INDEX_FILE = "books.json"

# ID-ul fix al grupului tău (extras direct din aplicație ca să nu mai dea erori)
ID_GRUP_REAL = 2597093808  

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Funcția CAUTA simplă și sigură - generează link-uri directe folosind ID-ul fix al grupului
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    if not context.args:
        await update.message.reply_text("Te rog scrie: /cauta [titlu sau autor]")
        return

    query = " ".join(context.args).lower()
    index = load_index()
    
    # Căutăm cărțile în baza de date
    results = [name for name in index if query in name.lower()]
    
    if results:
        text = "📚 *Cărți găsite în bibliotecă:*\n\n"
        
        for name in results[:5]:  # Afișăm primele 5 rezultate
            # Generăm link-ul direct folosind ID-ul fixat de noi
            link = f"https://t.me/c/{ID_GRUP_REAL}/{index[name]}"
            text += f"• [{name}]({link})\n"
            
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await update.message.reply_text("❌ Nu am găsit nicio carte cu acel titlu.")

# Inițializare aplicație - am scos complet funcția de scanare care dădea erori
app = ApplicationBuilder().token(TOKEN).build()

# Înregistrare singurei comenzi de care ai nevoie
app.add_handler(CommandHandler("cauta", search))

if __name__ == "__main__":
    app.run_polling()
