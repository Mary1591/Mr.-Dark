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

def save_index(index):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

# Funcția REPARATĂ COMPLET pentru scanarea istoricului
async def scaneaza_grup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if chat_member.status not in ['creator', 'administrator']:
        await update.message.reply_text("Doar administratorii pot rula această comandă.")
        return

    status_msg = await update.message.reply_text("🔄 Pornesc scanarea grupului pentru a citi fișierele... Te rog așteaptă.")
    index = load_index()
    numar_carti_gasite = 0
    
    offset_id = None
    limit = 100
    total_scanned = 0
    max_messages = 3000  

    try:
        while total_scanned < max_messages:
            # REPARARE: get_chat_history se apelează de pe update.effective_chat!
            messages = await update.effective_chat.get_chat_history(
                limit=limit,
                offset_id=offset_id
            )
            
            if not messages:
                break
                
            for message in messages:
                offset_id = message.message_id
                total_scanned += 1
                
                if message.document and message.document.file_name:
                    name = message.document.file_name
                    if name.lower().endswith((".epub", ".pdf", ".docx")):
                        index[name] = message.message_id
                        numar_carti_gasite += 1

        save_index(index)
        await status_msg.edit_text(f"✅ Scanare finalizată! Am găsit și salvat {numar_carti_gasite} cărți direct din istoricul acestui grup.")
    except Exception as e:
        await status_msg.edit_text(f"❌ A apărut o eroare la scanare: {str(e)}")

# Funcția CAUTA clasică (generează link-uri albastre)
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    if not context.args:
        await update.message.reply_text("Te rog scrie: /cauta [titlu sau autor]")
        return

    query = " ".join(context.args).lower()
    index = load_index()
    chat_id = update.message.chat_id
    
    results = [name for name in index if query in name.lower()]
    
    if results:
        clean_chat_id = str(chat_id).replace("-100", "")
        text = "📚 *Cărți găsite în bibliotecă:*\n\n"
        
        for name in results[:5]:  
            link = f"https://t.me/c/{clean_chat_id}/{index[name]}"
            text += f"• [{name}]({link})\n"
            
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await update.message.reply_text("❌ Nu am găsit nicio carte cu acel titlu.")

# Inițializare aplicație
app = ApplicationBuilder().token(TOKEN).build()

# Înregistrare comenzi
app.add_handler(CommandHandler("cauta", search))
app.add_handler(CommandHandler("scaneaza_grup", scaneaza_grup))

if __name__ == "__main__":
    app.run_polling()
