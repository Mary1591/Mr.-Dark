import os
import json
from telethon import TelegramClient, events

# Preluăm variabilele din sistem (Railway)
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
INDEX_FILE = "books_grup.json"

# ID-ul grupului tău (extras din link-urile tale anterioare)
ID_GRUP_REAL = 2597093808  

# Inițializăm clientul Telethon ca Userbot (se conectează cu token-ul de bot pentru comenzi, dar folosește API pentru scanare avansată)
client = TelegramClient('mr_dark_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

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

# Comandă specială pentru a forța scanarea totală a grupului
@client.on(events.NewMessage(pattern='/scaneaza'))
async def scaneaza_grup(event):
    # Verificăm dacă cel care dă comanda este admin (adică tu)
    permissions = await client.get_permissions(event.chat_id, event.sender_id)
    if not permissions.is_admin:
        await event.respond("❌ Doar administratorii pot rula această comandă.")
        return

    status_msg = await event.respond("🔄 Pornesc scanarea profundă a grupului... Caut toate cărțile postate în istoric.")
    index = load_index()
    numar_carti = 0

    # Telethon poate citi absolut tot istoricul fără limitări de versiune
    async for message in client.iter_messages(event.chat_id):
        if message.file and message.file.name:
            nume_fisier = message.file.name
            if nume_fisier.lower().endswith(('.epub', '.pdf', '.docx')):
                # Salvăm numele cărții și ID-ul exact de pe grup
                index[nume_fisier] = message.id
                numar_carti += 1

    save_index(index)
    await status_msg.edit(f"✅ Scanare completă! Am salvat {numar_carti} cărți cu ID-urile lor reale de pe grup.")

# Comanda clasică de căutare care generează link-uri albastre funcționale 100%
@client.on(events.NewMessage(pattern='/cauta (.+)'))
async def search(event):
    titlu_cautat = event.pattern_match.group(1).strip().lower()
    index = load_index()
    
    results = [name for name in index if titlu_cautat in name.lower()]
    
    if results:
        text = "📚 *Cărți găsite în bibliotecă:*\n\n"
        for name in results[:5]:  # Afișează primele 5 rezultate
            # Link-ul este construit direct cu ID-ul real al grupului și ID-ul mesajului scanat
            link = f"https://t.me/c/{ID_GRUP_REAL}/{index[name]}"
            text += f"• [{name}]({link})\n"
        
        await event.respond(text, parse_mode='markdown', link_preview=False)
    else:
        await event.respond("❌ Nu am găsit nicio carte cu acest titlu pe grup.")

print("Botul Mr. Dark (Telethon) a pornit cu succes!")
client.run_until_disconnected()
