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

# LISTA DI ENDPOINT DA PROVARE IN ORDINE
# Se il primo fallisce (404), passa al secondo.
MODEL_ENDPOINTS = [
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}",
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}",
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent?key={API_KEY}"
]

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

    payload = {
        "contents": [{
            "parts": [{
                "text": f"Agisci come Ricercatore Senior. Scrivi un REPORT ACCADEMICO (200 parole) su: '{title}'. Contesto: '{description}'. Regole: Titolo Saggistico nella prima riga, poi testo analitico."
            }]
        }]
    }
    data = json.dumps(payload).encode('utf-8')
    
    last_error = ""

    # CICLO DI TENTATIVI SUI DIVERSI MODELLI
    for url in MODEL_ENDPOINTS:
        try:
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # Se siamo qui, ha funzionato!
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
                except:
                    return title, "⚠️ L'IA ha risposto vuoto.", description
                    
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}"
            if e.code == 404:
                continue # Prova il prossimo modello
            else:
                # Se è un errore diverso (es. 403 Forbidden), inutile insistere
                return title, f"⚠️ ERRORE BLOCCANTE {e.code}: Controlla API Key.", description
        except Exception as e:
            last_error = str(e)
            continue

    return title, f"⚠️ TUTTI I MODELLI FALLITI. Ultimo errore: {last_error}", description

# --- ESECUZIONE ---
new_articles = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- START METODO MULTI-MODELLO ---")

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
    print("✅ DATABASE AGGIORNATO")
