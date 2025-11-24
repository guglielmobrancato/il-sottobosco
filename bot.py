import json
import urllib.request
import xml.etree.ElementTree as ET
import ssl
import os
import time
from datetime import datetime
import google.generativeai as genai

# --- RECUPERO CHIAVE ---
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- DEBUG INIZIALE ---
if not API_KEY:
    print("❌ ERRORE GRAVE: La chiave API_KEY non è stata trovata nelle variabili d'ambiente!")
    print("Il bot funzionerà in modalità 'solo copia-incolla' senza IA.")
else:
    print(f"✅ Chiave trovata! Lunghezza: {len(API_KEY)} caratteri. Configuro l'IA...")
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        print(f"❌ Errore configurazione Gemini: {e}")

SOURCES = {
    "geopolitica": "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml", # Priorità a geopolitica per test
    "tech": "https://www.ansa.it/sito/notizie/tecnologia/tecnologia_rss.xml"
}

ICONS = { "geopolitica": "fa-globe-europe", "tech": "fa-microchip" }

# --- GENERAZIONE ---
def generate_paper(title, description):
    # SE MANCA LA CHIAVE: Lo scriviamo nell'articolo per avvisarti
    if not API_KEY:
        return title, f"⚠️ SISTEMA OFFLINE: Chiave AI mancante. Controlla GitHub Secrets.\n\nNotizia originale: {description}", description

    prompt = f"""
    Agisci come Ricercatore Senior. Scrivi un'analisi accademica approfondita (250 parole) su:
    {title} - {description}
    
    Struttura: Titolo Saggistico, poi testo.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Gestione formattazione
        parts = text.split('\n', 1)
        if len(parts) > 1 and "Titolo" in parts[0]:
            new_title = parts[0].replace("Titolo:", "").strip()
            body = parts[1].strip()
        else:
            new_title = title
            body = text

        return new_title, body, " ".join(body.split()[:30]) + "..."

    except Exception as e:
        return title, f"⚠️ ERRORE IA: {str(e)}\n\n{description}", description

# --- ESECUZIONE ---
# Per il test, cancelliamo le news vecchie e ne scarichiamo solo 2 fresche
new_articles = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- START ---")
for cat, url in SOURCES.items():
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            item = tree.find(".//item") # Solo la prima per test veloce
            if item:
                title = item.find("title").text
                desc = item.find("description").text.split('<')[0].strip()
                
                # Cerca immagine
                img = ""
                enc = item.find("enclosure")
                if enc is not None and "image" in enc.get("type", ""): img = enc.get("url")

                print(f"Generazione per: {title}")
                new_title, body, excerpt = generate_paper(title, desc)

                new_articles.append({
                    "id": int(time.time()) + len(new_articles),
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "category": cat,
                    "author": "La Redazione",
                    "title": new_title,
                    "excerpt": excerpt,
                    "body": body,
                    "imageIcon": ICONS.get(cat, "fa-newspaper"),
                    "imageReal": img,
                    "link": item.find("link").text
                })
    except Exception as e:
        print(f"Errore {cat}: {e}")

# SALVATAGGIO (Sovrascrive tutto per test pulito)
if new_articles:
    with open("news.js", "w", encoding="utf-8") as f:
        f.write(f"const newsData = {json.dumps(new_articles, indent=4)};")
    print("✅ DATABASE AGGIORNATO.")
