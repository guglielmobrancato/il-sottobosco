import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import ssl
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE XAI (GROK) ---
API_KEY = os.environ.get("XAI_API_KEY")
API_URL = "https://api.x.ai/v1/chat/completions"

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

def generate_paper_grok(title, description):
    if not API_KEY:
        return title, "⚠️ ERRORE: Chiave XAI_API_KEY mancante.", description

    # Costruiamo la richiesta per Grok
    payload = {
        "model": "grok-beta", # O 'grok-2' se hai accesso
        "messages": [
            {
                "role": "system",
                "content": "Sei un ricercatore senior del think-tank 'Il Sottobosco'. Scrivi in italiano. Stile: Accademico, analitico, cinico, underground."
            },
            {
                "role": "user",
                "content": f"Scrivi un REPORT DI ANALISI (200 parole) su: '{title}'. Contesto: '{description}'. Regole: Prima riga TITOLO SAGGISTICO, poi vai a capo e scrivi il testo."
            }
        ],
        "temperature": 0.7
    }
    
    data = json.dumps(payload).encode('utf-8')
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        req = urllib.request.Request(API_URL, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # Leggiamo la risposta di Grok
            text = result['choices'][0]['message']['content'].strip()
            
            parts = text.split('\n', 1)
            if len(parts) > 1:
                new_title = parts[0].replace("Titolo:", "").replace('"', '').strip()
                body = parts[1].strip()
            else:
                new_title = title
                body = text
                
            return new_title, body, " ".join(body.split()[:30]) + "..."

    except urllib.error.HTTPError as e:
        return title, f"⚠️ ERRORE GROK {e.code}: {e.read().decode()}", description
    except Exception as e:
        return title, f"⚠️ ERRORE GENERICO: {str(e)}", description

# --- ESECUZIONE ---
new_articles = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- START GROK BOT ---")

for cat, url in SOURCES.items():
    try:
        print(f"Leggo {cat}...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            
            # Prime 2 notizie
            for item in tree.findall(".//item")[:2]:
                title = item.find("title").text
                d = item.find("description")
                desc = d.text.split('<')[0].strip() if d is not None else ""
                
                img = ""
                enc = item.find("enclosure")
                if enc is not None and "image" in enc.get("type", ""): img = enc.get("url")

                print(f" -> Invio a Grok: {title[:20]}...")
                new_title, body, excerpt = generate_paper_grok(title, desc)

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
                time.sleep(1) 
    except Exception as e:
        print(f"Errore {cat}: {e}")

if new_articles:
    json_data = json.dumps(new_articles, indent=4)
    with open("news.js", "w", encoding="utf-8") as f:
        f.write(f"const newsData = {json_data};")
    print("✅ DATABASE AGGIORNATO CON GROK")
