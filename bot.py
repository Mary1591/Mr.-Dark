async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text("Te rog scrie: /cauta [titlu sau autor]")
        return

    # Luăm cuvintele căutate și le punem într-o listă (ex: ['the', 'predator', 'runyx'])
    search_words = [word.lower() for word in context.args]
    index = load_index()
    results = []

    if isinstance(index, list):
        for item in index:
            if isinstance(item, dict) and "title" in item:
                book_title = item["title"].lower()
                msg_id = item.get("id", "0")
                
                # TRUCUL: Verificăm dacă ABSOLUT TOATE cuvintele căutate se află în titlu
                if all(word in book_title for word in search_words):
                    results.append((item["title"], msg_id))
                    
    elif isinstance(index, dict):
        for msg_id, data in index.items():
            book_title = ""
            if isinstance(data, dict) and "title" in data:
                book_title = data["title"].lower()
            elif isinstance(data, dict) and "name" in data:
                book_title = data["name"].lower()
            elif isinstance(data, str):
                book_title = data.lower()
                
            if book_title and all(word in book_title for word in search_words):
                if isinstance(data, dict):
                    results.append((data.get("title") or data.get("name"), msg_id))
                else:
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
        await update.message.reply_text("❌ Nu am găsit nicio carte care să conțină aceste cuvinte în bibliotecă.")
