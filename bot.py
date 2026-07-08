import json
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
INDEX_FILE = "books.json"
ID_GRUP_MARE = 1957960999  
SECRET_KEY = "maria_secret_key_2026" 
CARTI_PER_PAGINA = 30

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def curata_text_standard(text):
    if not text:
        return ""
    text_lower = text.lower()
    caractere_de_sters = ["_", "-", ".", ",", "&", "/", "\\", "(", ")", "[", "]"]
    for caracter in caractere_de_sters:
        text_lower = text_lower.replace(caracter, " ")
    return text_lower

def curata_text_complet(text):
    if not text:
        return ""
    text_lower = text.lower()
    caractere_de_sters = ["_", "-", ".", ",", "&", "/", "\\", "(", ")", "[", "]", " "]
    for caracter in caractere_de_sters:
        text_lower = text_lower.replace(caracter, "")
    return text_lower

def executa_cautare(query_text):
    """Funcție separată care caută în baza de date pe loc, de fiecare dată când se schimbă pagina"""
    query_standard = curata_text_standard(query_text)
    search_words = [word for word in query_standard.split() if word]
    query_complet_legat = curata_text_complet(query_text)
    
    index = load_index()
    results = []

    def se_potriveste(book_title):
        if not book_title:
            return False
        
        title_standard = curata_text_standard(book_title)
        title_complet_legat = curata_text_complet(book_title)
        
        if len(query_complet_legat) > 1 and query_complet_legat in title_complet_legat:
            if query_complet_legat == "ward":
                return bool(re.search(r'\bward\b', title_standard))
            return True
            
        if search_words:
            for word in search_words:
                if not re.search(r'\b' + re.escape(word) + r'\b', title_standard):
                    return False
            return True
                
        return False

    if isinstance(index, list):
        for item in index:
            if isinstance(item, dict) and "title" in item:
                title_original = item["title"]
                msg_id = item.get("id", "0")
                if se_potriveste(title_original):
                    results.append((title_original, msg_id))
                    
    elif isinstance(index, dict):
        for msg_id, data in index.items():
            book_title = ""
            if isinstance(data, dict) and "title" in data:
                book_title = data["title"]
            elif isinstance(data, dict) and "name" in data:
                book_title = data["name"]
            elif isinstance(data, str):
                book_title = data
                
            if book_title and se_potriveste(book_title):
                if isinstance(data, dict):
                    results.append((data.get("title") or data.get("name"), msg_id))
                else:
                    results.append((data, msg_id))

    rezultate_unice = []
    vazute = set()
    for t, m in results:
        if m not in vazute:
            vazute.add(m)
            rezultate_unice.append((t, m))
            
    return rezultate_unice

def genereaza_pagina_text_si_butoane(results, pagina, query_text):
    total_rezultate = len(results)
    start_idx = pagina * CARTI_PER_PAGINA
    end_idx = start_idx + CARTI_PER_PAGINA
    lista_pagina = results[start_idx:end_idx]
    
    total_pagini = (total_rezultate + CARTI_PER_PAGINA - 1) // CARTI_PER_PAGINA

    text = f"📚 *Cărți găsite pentru „{query_text}”:*\n"
    text += f"📖 *Pagina {pagina + 1} din {total_pagini}* (Total cărți: {total_rezultate})\n\n"
    
    for title, msg_id in lista_pagina:
        link = f"https://t.me/c/{ID_GRUP_MARE}/{msg_id}"
        text += f"• [{title}]({link})\n"

    # Limităm textul salvat în buton ca să nu depășească limita Telegram (max 64 caractere în callback_data)
    query_scurtat = query_text[:30]

    butoane = []
    if pagina > 0:
        # Salvăm pagina și textul căutat direct în buton! zero memorie volatilă
        butoane.append(InlineKeyboardButton("⬅️ Înapoi", callback_data=f"pag_{pagina-1}_{query_scurtat}"))
    if end_idx < total_rezultate:
        butoane.append(InlineKeyboardButton("Înainte ➡️", callback_data=f"pag_{pagina+1}_{query_scurtat}"))

    tastatura = InlineKeyboardMarkup([butoane]) if butoane else None
    return text, tastatura

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text("Te rog scrie: /cauta [titlu sau autor]")
        return

    query_text = " ".join(context.args)
    results = executa_cautare(query_text)

    if results:
        text, tastatura = genereaza_pagina_text_si_butoane(results, 0, query_text)
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=tastatura)
    else:
        await update.message.reply_text(f"❌ Nu am găsit nicio carte care să conțină „{query_text}” în bibliotecă.")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
        
    await query.answer()

    # Despicăm comanda butonului: ex. pag_1_ward
    parts = query.data.split("_")
    
    if len(parts) >= 3 and parts[0] == "pag":
        pagina_noua = int(parts[1])
        # Reconstruim textul căutat extras direct din interiorul butonului
        query_text_salvat = "_".join(parts[2:])
        
        # Căutăm din nou pe loc, strict pe baza textului scris în buton!
        results = executa_cautare(query_text_salvat)

        if results:
            text, tastatura = genereaza_pagina_text_si_butoane(results, pagina_noua, query_text_salvat)
            await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=tastatura)

async def update_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.document:
        return
    
    if context.args and context.args[0] == SECRET_KEY:
        file = await context.message.document.get_file()
        await file.download_to_drive(INDEX_FILE)
        await update.message.reply_text("✅ Baza de date a fost actualizată cu succes în privat!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("cauta", search))
    app.add_handler(CommandHandler("update_books", update_db))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Botul pornește și curăță sesiunile vechi...")
    app.run_polling(drop_pending_updates=True)
