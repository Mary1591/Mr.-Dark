
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

# Ofertă de ajutor: Comandă admin pentru a scana grupul și a lua ID-urile corecte din grup
async def scaneaza_grup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Permitem doar adminilor să pornească scanarea
    chat_member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if chat_member.status not in ['creator', 'administrator']:
        await update.message.reply_text("Doar administratorii pot rula această comandă.")
        return

    status_msg = await update.message.reply_text("🔄 Pornesc scanarea grupului pentru a citi fișierele existente... Te rog așteaptă.")
    index = load_index()
    numar_carti_gasite = 0

    try:
        # Botul citește ultimele 3000 de mesaje din istoric (ajustează numărul dacă grupul e mai mare)
        async for message in context.bot.get_chat_history(chat_id=update.effective_chat.id, limit=3000):
            if message.document and message.document.file_name:
                name = message.document.file_name
                if name.lower().endswith((".epub", ".pdf", ".docx")):
                    # Salvăm ID-ul exact al mesajului de pe GRUP
                    index[name] = message.message_id
                    numar_carti_gasite += 1

        save_index(index)
        await status_msg.edit_text(f"✅ Scanare finalizată! Am găsit și salvat {numar_carti_gasite} cărți direct din istoricul acestui grup.")
    except Exception as e:
        await status_msg.edit_text(f"❌ A apărut o eroare la scanare: {str(e)}")

# Funcția CAUTA: generează link-uri albastre folosind ID-urile din grup
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
