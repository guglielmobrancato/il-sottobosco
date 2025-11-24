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

if API_KEY:
    genai.configure(api_key=API_KEY)
    # --- LA CORREZIONE È QUI SOTTO ---
    # Usiamo 'gemini-1.5-flash' che è il modello standard attuale
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("⚠️ Chiave mancante.")

SOURCES = {
    "geopolitica": "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml",
    "tech": "https://www.ansa.it/sito/notizie/tecnologia/tecnologia_rss.xml",
    "cronaca": "https://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml"
}

ICONS = { 
    "geopolitica": "fa-globe-europe", 
    "tech": "fa-microchip",
    "cronaca": "fa-user-secret"
}

def generate_paper(title, description):
    if not API_KEY:
        return title, f"⚠️ ERRORE: Chiave non trovata.\n{description}", description

    prompt = f"""
    Agisci come Ricercatore Senior del think-tank 'Il Sottobosco'.
    Scrivi un REPORT DI ANALISI (circa 250 parole) su: "{title}".
    Contesto di partenza: "{description}".
    
    Linee Guida:
    1. Tono: Accademico, analitico, autorevole.
    2. Contenuto: Analizza le implicazioni future e fai un parallelo storico.
    3. Formattazione: Titolo Saggistico nella prima riga, poi il testo completo.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        parts = text.split('\n', 1)
        if len(parts) > 1 and len(parts[0]) < 100:
            new_title = parts[0].replace("Titolo:", "").replace("*", "").strip()
            body = parts[1].strip()
        else:
            new_title = title
            body = text

        return new_title, body, " ".join(body.split()[:30]) + "..."

    except Exception as e:
        return title, f"⚠️ ERRORE IA: {str(e)}\n\n{description}", description

# --- ESECUZIONE ---
new_articles = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- START FIX 1.5 ---")

for cat, url in SOURCES.items():
    try:
        print(f"Scaricando {cat}...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            
            # Prendiamo le prime 2 notizie per categoria
            for item in tree.findall(".//item")[:2]:
                title = item.find("title").text
                d = item.find("description")
                desc = d.text.split('<')[0].strip() if d is not None else ""
                
                img = ""
                enc = item.find("enclosure")
                if enc is not None and "image" in enc.get("type", ""): img = enc.get("url")

                print(f" -> Genero Paper su: {title[:20]}...")
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
                time.sleep(2) # Pausa importante
    except Exception as e:
        print(f"Errore {cat}: {e}")

# SALVATAGGIO
if new_articles:
    json_data = json.dumps(new_articles, indent=4)
    with open("news.js", "w", encoding="utf-8") as f:
        f.write(f"const newsData = {json_data};")
    print("✅ DATABASE AGGIORNATO CON GEMINI 1.5")

