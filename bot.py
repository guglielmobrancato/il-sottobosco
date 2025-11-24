import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import ssl
import os
import time
import random
from datetime import datetime

# --- CONFIGURAZIONE ---
API_KEY = os.environ.get("GEMINI_API_KEY")
# Usiamo l'endpoint standard di Gemini 1.5 Flash
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

# --- GENERATORE DI RISERVA (FALLBACK) ---
# Se l'IA fallisce, il bot usa queste frasi per costruire l'articolo
FALLBACK_TEMPLATES = [
    "In merito ai recenti sviluppi riguardanti {title}, emerge un quadro complesso. Fonti accreditate riportano che {desc}. Questo evento potrebbe segnare un punto di svolta significativo per il settore.",
    "L'attenzione degli analisti si concentra oggi su: {title}. Come riportato dalle agenzie, {desc}. È fondamentale osservare le ripercussioni a lungo termine di questa dinamica.",
    "Un nuovo capitolo si apre con la notizia: {title}. I dettagli attuali indicano che {desc}. Resta da capire come gli attori coinvolti reagiranno nelle prossime ore."
]

def clean_text(text):
    if not text: return ""
    return text.split('<')[0].strip()

def generate_paper_safe(title, description):
    # TENTATIVO 1: USARE L'IA DI GOOGLE
    if API_KEY:
        try:
            payload = {
                "contents": [{
                    "parts": [{"text": f"Scrivi un report analitico di 150 parole su: '{title}'. Contesto: '{description}'. Metti il titolo saggistico nella prima riga."}]
                }]
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(API_URL, data=data, headers={'Content-Type': 'application/json'})
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                
                parts = text.split('\n', 1)
                new_title = parts[0].replace("Titolo:", "").replace("*", "").strip() if len(parts) > 1 else title
                body = parts[1].strip() if len(parts) > 1 else text
                
                return new_title, body, " ".join(body.split()[:25]) + "..."
        except Exception:
            pass # Se l'IA fallisce, IGNORA L'ERRORE e passa al Piano B

    # TENTATIVO 2 (PIANO B): GENERAZIONE PROCEDURALE
    # Se siamo qui, l'IA ha fallito. Costruiamo l'articolo a mano.
    print(f"   ⚠️ IA non disponibile. Uso generatore di riserva per: {title[:15]}...")
    
    template = random.choice(FALLBACK_TEMPLATES)
    body = template.format(title=title, desc=description)
    
    # Aggiungiamo un po' di "sapore" accademico generico alla fine
    body += "\n\nGli esperti suggeriscono cautela nell'interpretazione di questi dati preliminari. La situazione è in evoluzione e richiederà ulteriori approfondimenti nei prossimi giorni per comprendere appieno la portata dell'accaduto."
    
    return title, body, description[:100] + "..."

# --- ESECUZIONE ---
new_articles = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- AVVIO BOT INDISTRUTTIBILE ---")

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
                desc = clean_text(d.text) if d is not None else "Dettagli in aggiornamento."
                
                img = ""
                enc = item.find("enclosure")
                if enc is not None and "image" in enc.get("type", ""): img = enc.get("url")

                # Generazione (Sicura al 100%)
                new_title, body, excerpt = generate_paper_safe(title, desc)

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
        print(f"Errore RSS {cat}: {e}")

# SALVATAGGIO
if new_articles:
    json_data = json.dumps(new_articles, indent=4)
    with open("news.js", "w", encoding="utf-8") as f:
        f.write(f"const newsData = {json_data};")
    print("✅ DATABASE AGGIORNATO (Modalità Sicura)")
