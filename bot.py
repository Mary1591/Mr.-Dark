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
                return []
    return []

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text("Te rog scrie: /cauta [titlu sau autor]")
        return

    query = " ".join(context.args).lower()
    index = load_index()
    results = []

    if isinstance(index, list):
        for item in index:
            if isinstance(item, dict) and "title" in item:
                book_title = item["title"]
                msg_id = item.get("id", "0")
                if query in book_title.lower():
                    results.append((book_title, msg_id))
                    
    elif isinstance(index, dict):
        for msg_id, data in index.items():
            if isinstance(data, dict) and "title" in data:
                book_title = data["title"]
                if query in book_title.lower():
                    results.append((book_title, msg_id))
            elif isinstance(data, dict) and "name" in data:
                book_title = data["name"]
                if query in book_title.lower():
                    results.append((book_title, msg_id))
            elif isinstance(data, str):
                if query in data.lower():
                    results.append((data, msg_id))

    if results:
        text = "📚 *Cărți găsite în bibliotecă:*\n\n"
        for title, msg_id in results[:30]:  
            link = f"https://t.me/c/{ID_GRUP_MARE}/{msg_id}"
            text += f"• [{title}]({link})\n"
            
        if len(results) > 30:
            text += f"\n⚠️ *S-au găsit în total {len(results)} rezultate. Specifică mai multe cuvinte dacă nu vezi cartea ta.*"
            
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await update.message.reply_text("❌ Nu am găsit nicio carte cu acest titlu în bibliotecă.")

async def update_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.document:
        return
    
    if context.args and context.args[0] == SECRET_KEY:
        file = await context.message.document.get_file()
        await file.download_to_drive(INDEX_FILE)
        await update.message.reply_text("✅ Baza de date a fost actualizată cu succes în privat!")

if __name__ == "__main__":
    # Construim aplicația standard
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Adăugăm comenzile
    app.add_handler(CommandHandler("cauta", search))
    app.add_handler(CommandHandler("update_books", update_db))
    
    # Pornim botul și îi spunem direct să șteargă orice update-uri/conexiuni vechi agățate (drop_pending_updates=True)
    print("Botul pornește și curăță sesiunile vechi...")
    app.run_polling(drop_pending_updates=True)
