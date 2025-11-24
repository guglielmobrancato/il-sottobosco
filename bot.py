import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import ssl
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
API_KEY = os.environ.get("GEMINI_API_KEY")

# URL DIRETTO ALLE API DI GOOGLE (Bypassa la libreria Python)
# Usiamo il modello Flash che è veloce e gratuito
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

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

def generate_paper_manual(title, description):
    if not API_KEY:
        return title, "⚠️ ERRORE: Chiave mancante.", description

    # 1. Costruiamo il pacchetto dati (JSON) a mano
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Agisci come Ricercatore Senior. Scrivi un REPORT ACCADEMICO (200 parole) su: '{title}'. Contesto: '{description}'. Regole: Titolo Saggistico nella prima riga, poi testo analitico."
            }]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    
    try:
        # 2. Spediamo la richiesta (POST)
        req = urllib.request.Request(API_URL, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # 3. Leggiamo la risposta grezza
            try:
                text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                
                parts = text.split('\n', 1)
                if len(parts) > 1:
                    new_title = parts[0].replace("Titolo:", "").replace("*", "").strip()
                    body = parts[1].strip()
                else:
                    new_title = title
                    body = text
                    
                return new_title, body, " ".join(body.split()[:30]) + "..."
                
            except (KeyError, IndexError):
                return title, "⚠️ L'IA ha risposto ma il formato è vuoto (Safety Block).", description

    except urllib.error.HTTPError as e:
        # Qui catturiamo l'errore esatto se Google ci blocca
        error_body = e.read().decode()
        return title, f"⚠️ ERRORE HTTP {e.code}: {error_body}", description
    except Exception as e:
        return title, f"⚠️ ERRORE GENERICO: {str(e)}", description

# --- ESECUZIONE ---
new_articles = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- START METODO DIRETTO (REST) ---")

for cat, url in SOURCES.items():
    try:
        print(f"Leggo {cat}...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            
            for item in tree.findall(".//item")[:2]:
                title = item.find("title").text
                d = item.find("description")
                desc = d.text.split('<')[0].strip() if d is not None else ""
                
                img = ""
                enc = item.find("enclosure")
                if enc is not None and "image" in enc.get("type", ""): img = enc.get("url")

                print(f" -> Invio a Google: {title[:20]}...")
                new_title, body, excerpt = generate_paper_manual(title, desc)

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
    print("✅ DATABASE AGGIORNATO VIA REST API")
