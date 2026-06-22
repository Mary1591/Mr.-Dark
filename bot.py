import json
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
INDEX_FILE = "books.json"

# ID-ul canalului tău arhivă (unde sunt stocate cărțile mutate de scanner)
# Schimbă acest număr cu cel real dacă este diferit!
ID_CANAL_ARHIVA = -1004470118642  

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

# Funcție secundară care rulează în fundal pentru a șterge mesajul după 5 minute
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
    if not doc.file_name.lower().endswith((".epub", ".pdf", ".docx")):
        return

    index = load_index()
    name = doc.file_name
    chat_id = update.message.chat_id
    msg_id = update.message.message_id

    if name in index:
        # Ștergem fișierul duplicat trimis de membru
        try:
            await update.message.delete()
        except Exception:
            pass 

        # Generăm link-ul către postarea originală
        clean_chat_id = str(chat_id).replace("-100", "")
        original_link = f"https://t.me/c/{clean_chat_id}/{index[name]}"
        
        warning = await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ *CARTE DEJA POSTATĂ*\n\nFișierul `{name}` există deja.\n"
                 f"👉 O poți găsi aici: {original_link}\n\n_(Acest mesaj va fi șters în 5 minute)_",
            parse_mode="Markdown"
        )
        
        # Programăm ștergerea mesajului după 300 de secunde
        context.job_queue.run_once(delete_message_job, 300, chat_id=chat_id, data=warning.message_id)
    else:
        index[name] = msg_id
        save_index(index)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    if not context.args:
        await update.message.reply_text("Te rog scrie: /cauta [titlu]")
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

# Funcția nouă care caută titlul în books.json și REPOSTEAZĂ fișierul direct în chat
async def cauta_carte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text("Te rog scrie și titlul cărții. Exemplu: /carte Nume Carte")
        return

    titlu_cautat = " ".join(context.args).strip().lower()
    
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            biblioteca = json.load(f)
        
        id_mesaj_arhiva = None
        nume_real_carte = None
        
        # Căutăm cartea în fișier (fără să conteze literele mari/mici)
        for nume_carte, id_mesaj in biblioteca.items():
            if titlu_cautat in nume_carte.lower():
                id_mesaj_arhiva = id_mesaj
                nume_real_carte = nume_carte
                break
        
        if id_mesaj_arhiva:
            await update.message.reply_text(f"Am găsit! Trimit acum: {nume_real_carte}... 📚")
            try:
                # Botul ia mesajul/fișierul din canalul arhivă și îl repostează în grupul unde a fost cerut
                await context.bot.forward_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=ID_CANAL_ARHIVA,
                    message_id=id_mesaj_arhiva
                )
            except Exception as e:
                await update.message.reply_text("Ups, a apărut o eroare la repostarea cărții. Asigură-te că botul este administrator în canalul arhivă.")
        else:
            await update.message.reply_text("Nu am găsit această carte în bibliotecă. Verifică dacă ai scris numele corect!")
    else:
        await update.message.reply_text("Baza de date cu cărți nu este disponibilă momentan.")

# Inițializare aplicație
app = ApplicationBuilder().token(TOKEN).build()

# Înregistrare comenzi
app.add_handler(CommandHandler("cauta", search))
app.add_handler(CommandHandler("carte", cauta_carte))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

# Pornire bot
if __name__ == "__main__":
    app.run_polling()
