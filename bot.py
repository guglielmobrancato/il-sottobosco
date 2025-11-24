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

# Configurazione IA
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    print("⚠️ ATTENZIONE: Chiave API mancante. Funzionerà solo in copia-incolla.")

SOURCES = {
    "geopolitica": "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml",
    "tech": "https://www.ansa.it/sito/notizie/tecnologia/tecnologia_rss.xml"
}

ICONS = { "geopolitica": "fa-globe-europe", "tech": "fa-microchip" }

def generate_paper(title, description):
    if not API_KEY:
        return title, f"⚠️ ERRORE: Chiave GitHub non trovata. Controlla i Secrets.\n\n{description}", description

    prompt = f"""
    Agisci come Ricercatore Senior. Scrivi un report accademico (200 parole) su:
    {title}
    
    Contesto: {description}
    
    Regole:
    1. Stile saggistico.
    2. Inserisci un riferimento storico.
    3. Output: Titolo nella prima riga, poi il testo.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        parts = text.split('\n', 1)
        if len(parts) > 1:
            new_title = parts[0].replace("Titolo:", "").strip()
            body = parts[1].strip()
        else:
            new_title = title
            body = text
            
        return new_title, body, " ".join(body.split()[:25]) + "..."
    except Exception as e:
        return title, f"⚠️ Errore IA: {str(e)}", description

# --- ESECUZIONE (RESET TOTALE OGNI VOLTA) ---
new_articles = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- FORZATURA AGGIORNAMENTO ---")

for cat, url in SOURCES.items():
    try:
        print(f"Scaricando {cat}...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            
            # Prende la prima notizia
            item = tree.find(".//item")
            if item:
                title = item.find("title").text
                # Pulizia descrizione
                d = item.find("description")
                desc = d.text.split('<')[0].strip() if d is not None else ""
                
                # Immagine
                img = ""
                enc = item.find("enclosure")
                if enc is not None and "image" in enc.get("type", ""): img = enc.get("url")

                print(f"Generazione IA per: {title[:30]}...")
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
                time.sleep(2) # Pausa breve
    except Exception as e:
        print(f"Errore {cat}: {e}")

# SALVATAGGIO FORZATO
# Aggiungiamo un commento con l'orario per costringere Git a vedere una modifica
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
json_content = json.dumps(new_articles, indent=4)
file_content = f"const newsData = {json_content};\n// Ultimo aggiornamento forzato: {timestamp}"

with open("news.js", "w", encoding="utf-8") as f:
    f.write(file_content)

print("✅ FILE RISCRITTO DA ZERO. ORA GITHUB DOVRÀ AGGIORNARE.")
