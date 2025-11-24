import json
import urllib.request
import xml.etree.ElementTree as ET
import ssl
import os
import random
import time
from datetime import datetime
import google.generativeai as genai

# --- CONFIGURAZIONE ---
# Recupera la chiave segreta da GitHub
API_KEY = os.environ.get("GEMINI_API_KEY")

# Se non c'è la chiave (test locale), lo script si ferma o usa una stringa vuota
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')

SOURCES = {
    "cronaca": "https://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml",
    "geopolitica": "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml",
    "tech": "https://www.ansa.it/sito/notizie/tecnologia/tecnologia_rss.xml",
    "arte": "https://www.ansa.it/sito/notizie/cultura/cultura_rss.xml"
}

ICONS = {
    "cronaca": "fa-user-secret",
    "geopolitica": "fa-globe-europe",
    "tech": "fa-microchip",
    "arte": "fa-film",
    "difesa": "fa-shield-alt"
}

FAKE_AUTHORS = [
    "Dario 'Vipera' Neri", "Elena Sarti", "L'Osservatore", "Max V.", 
    "Giulia R.", "Il Corvo", "Dr. Mantis"
]

# --- FUNZIONE: RISCRITTURA CON IA ---
def rewrite_with_ai(title, description):
    if not API_KEY:
        return description # Se non c'è AI, restituisce l'originale
    
    prompt = f"""
    Sei un giornalista underground del blog 'Il Sottobosco'.
    Riscrivi questa notizia in italiano.
    Stile: Sintetico, diretto, leggermente cinico o misterioso. Max 40 parole.
    
    Notizia Originale: {title} - {description}
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return description # Fallback in caso di errore

# --- STEP 1: CARICA ARCHIVIO ESISTENTE ---
# Proviamo a leggere il file news.js esistente per non cancellare la storia
try:
    with open("news.js", "r", encoding="utf-8") as f:
        content = f.read()
        # Rimuoviamo "const newsData = " e ";" per ottenere solo il JSON
        json_str = content.replace("const newsData = ", "").replace(";", "")
        archive = json.loads(json_str)
except:
    archive = []

print(f"📚 Articoli in archivio: {len(archive)}")

# Lista dei link già presenti per evitare duplicati
existing_links = [item['link'] for item in archive]
new_articles = []

# --- STEP 2: SCARICA E PROCESSA ---
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- INIZIO SCANSIONE INTELLIGENTE ---")

for cat, url in SOURCES.items():
    try:
        print(f"📡 Analizzo {cat}...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            
            # Prende solo la PRIMA notizia più recente per categoria
            item = tree.find(".//item") 
            if item:
                link = item.find("link").text
                
                # Se la notizia è già in archivio, la saltiamo
                if link in existing_links:
                    print("   -> Già in archivio. Salto.")
                    continue

                title = item.find("title").text
                desc_obj = item.find("description")
                desc = desc_obj.text if desc_obj is not None else ""
                raw_desc = desc.split('<')[0].strip()

                print("   -> 🧠 Riscrivo con IA...")
                ai_text = rewrite_with_ai(title, raw_desc)
                
                # Creiamo il nuovo oggetto notizia
                new_article = {
                    "id": int(time.time()), # ID unico basato sull'orario
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "category": cat,
                    "author": random.choice(FAKE_AUTHORS),
                    "title": title,
                    "excerpt": ai_text,
                    "imageIcon": ICONS.get(cat, "fa-newspaper"),
                    "link": link # Manteniamo il link fonte per correttezza, o mettiamo "#"
                }
                
                new_articles.append(new_article)
                time.sleep(2) # Pausa per non intasare l'IA

    except Exception as e:
        print(f"Errore su {cat}: {e}")

# --- STEP 3: AGGIORNA E SALVA ---
if new_articles:
    print(f"✅ Trovati {len(new_articles)} nuovi articoli.")
    # Mette i nuovi in cima + i vecchi sotto
    updated_archive = new_articles + archive
    
    # Manteniamo l'archivio pulito: teniamo solo ultimi 50 articoli
    updated_archive = updated_archive[:50]

    json_data = json.dumps(updated_archive, indent=4)
    file_content = f"const newsData = {json_data};"

    with open("news.js", "w", encoding="utf-8") as f:
        f.write(file_content)
else:
    print("💤 Nessuna nuova notizia trovata.")

print("--- FINE ---")
