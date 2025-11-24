import json
import urllib.request
import xml.etree.ElementTree as ET
import ssl
import os
import time
from datetime import datetime
import google.generativeai as genai

# --- CONFIGURAZIONE ---
API_KEY = os.environ.get("GEMINI_API_KEY")

# Lista di modelli da tentare in ordine di preferenza
MODELS_TO_TRY = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.0-pro', 'gemini-pro']
ACTIVE_MODEL = None

if API_KEY:
    genai.configure(api_key=API_KEY)
    print(f"📚 Versione Libreria Google: {genai.__version__}")
    
    # TEST DI CONNESSIONE AL MODELLO
    print("--- TEST MODELLI DISPONIBILI ---")
    for model_name in MODELS_TO_TRY:
        try:
            print(f"Tentativo con {model_name}...", end=" ")
            m = genai.GenerativeModel(model_name)
            # Facciamo una domanda dummy per vedere se risponde
            m.generate_content("Ciao") 
            ACTIVE_MODEL = m
            print(f"✅ FUNZIONA! Useremo questo.")
            break
        except Exception as e:
            print(f"❌ Fallito ({e})")
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
    if not ACTIVE_MODEL:
        return title, f"⚠️ ERRORE: Nessun modello IA disponibile.\n{description}", description

    prompt = f"""
    Agisci come Ricercatore Senior del think-tank 'Il Sottobosco'.
    Scrivi un REPORT DI ANALISI (250 parole) su: "{title}".
    Contesto: "{description}".
    
    Linee Guida:
    1. Tono: Accademico e analitico.
    2. Struttura: Titolo Saggistico nella prima riga, poi il testo.
    """
    
    try:
        response = ACTIVE_MODEL.generate_content(prompt)
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
        return title, f"⚠️ ERRORE GENERAZIONE: {str(e)}\n\n{description}", description

# --- ESECUZIONE ---
new_articles = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- INIZIO SCANSIONE ---")

for cat, url in SOURCES.items():
    try:
        print(f"Scaricando {cat}...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            
            # Prendiamo le prime 2 notizie
            for item in tree.findall(".//item")[:2]:
                title = item.find("title").text
                d = item.find("description")
                desc = d.text.split('<')[0].strip() if d is not None else ""
                
                img = ""
                enc = item.find("enclosure")
                if enc is not None and "image" in enc.get("type", ""): img = enc.get("url")

                if ACTIVE_MODEL:
                    print(f" -> Genero Paper su: {title[:20]}...")
                    new_title, body, excerpt = generate_paper(title, desc)
                else:
                    new_title, body, excerpt = title, desc, desc

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
                time.sleep(2) 
    except Exception as e:
        print(f"Errore {cat}: {e}")

# SALVATAGGIO
if new_articles:
    json_data = json.dumps(new_articles, indent=4)
    with open("news.js", "w", encoding="utf-8") as f:
        f.write(f"const newsData = {json_data};")
    print("✅ DATABASE AGGIORNATO")

