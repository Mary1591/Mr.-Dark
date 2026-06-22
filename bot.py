import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
INDEX_FILE = "books.json"

# ID-ul real al canalului tău arhivă
ID_CANAL_ARHIVA = -1002597093808  

# Funcția CAUTA: caută în books.json și REPOSTEAZĂ fișierul direct în chat
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text("Te rog scrie și titlul cărții. Exemplu: /cauta Nume Carte")
        return

    titlu_cautat = " ".join(context.args).strip().lower()
    
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            biblioteca = json.load(f)
        
        id_mesaj_arhiva = None
        nume_real_carte = None
        
        # Căutăm cartea în biblioteca salvată
        for nume_carte, id_mesaj in biblioteca.items():
            if titlu_cautat in nume_carte.lower():
                id_mesaj_arhiva = id_mesaj
                nume_real_carte = nume_carte
                break
        
        if id_mesaj_arhiva:
            await update.message.reply_text(f"Am găsit! Trimit acum: {nume_real_carte}... 📚")
            try:
                # Botul ia fișierul din canalul arhivă și îl trimite direct pe grup
                await context.bot.forward_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=ID_CANAL_ARHIVA,
                    message_id=id_mesaj_arhiva
                )
            except Exception as e:
                await update.message.reply_text("Ups, a apărut o eroare la repostarea cărții. Asigură-te că botul este administrator în canalul arhivă.")
        else:
            await update.message.reply_text("❌ Nu am găsit această carte în bibliotecă. Verifică dacă ai scris numele corect!")
    else:
        await update.message.reply_text("Baza de date cu cărți nu este disponibilă momentan.")

# Inițializare aplicație simplificată (fără JobQueue și fără scanare documente)
app = ApplicationBuilder().token(TOKEN).build()

# Înregistrare singurei comenzi necesare
app.add_handler(CommandHandler("cauta", search))

# Pornire bot
if __name__ == "__main__":
    app.run_polling()
