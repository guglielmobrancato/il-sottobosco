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
    "arte": "fa-book",
    "difesa": "fa-shield-alt"
}

# --- FUNZIONE: GENERAZIONE ROBUSTA ---
def generate_academic_paper(title, description):
    if not API_KEY: return title, description, description 
    
    prompt = f"""
    Agisci come un Ricercatore Senior del centro studi 'Il Sottobosco'.
    Scrivi un REPORT DI ANALISI (circa 250 parole) partendo da questa notizia.
    
    Linee Guida:
    1. Tono: Accademico, distaccato, analitico.
    2. Struttura: Titolo saggistico -> Abstract -> Corpo.
    3. Inserisci un'analogia storica o filosofica.
    
    Notizia Fonte: {title} - {description}
    
    Output richiesto: 
    Titolo: [Il Tuo Titolo Qui]
    Corpo: [Il Testo Qui]
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # LOGICA BLINDATA: Se l'IA non usa il formato giusto, non rompiamo tutto.
        new_title = title
        body = text

        # Proviamo a estrarre il titolo se l'IA ha seguito le istruzioni
        lines = text.split('\n')
        if len(lines) > 0 and "Titolo:" in lines[0]:
            new_title = lines[0].replace("Titolo:", "").replace("*", "").strip()
            # Uniamo il resto come corpo, saltando la prima riga
            body = "\n".join(lines[1:]).replace("Corpo:", "").strip()
        
        # Creiamo estratto
        excerpt = " ".join(body.split()[:30]) + "..."
        
        return new_title, body, excerpt
    except Exception as e:
        print(f"⚠️ Errore IA su {title}: {e}")
        return title, description, "..."

# --- STEP 1: CARICA ARCHIVIO ---
try:
    with open("news.js", "r", encoding="utf-8") as f:
        content = f.read()
        json_str = content.replace("const newsData = ", "").replace(";", "")
        archive = json.loads(json_str)
except:
    archive = []

existing_links = [item['link'] for item in archive]
new_articles = []

# --- STEP 2: SCARICA E PROCESSA ---
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- INIZIO SCANSIONE ---")

for cat, url in SOURCES.items():
    try:
        print(f"📡 {cat}...", end=" ")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            
            # Prende la prima notizia
            item = tree.find(".//item") 
            if item:
                link = item.find("link").text
                
                if link in existing_links:
                    print("-> Già presente.")
                    continue

                title = item.find("title").text
                desc_obj = item.find("description")
                raw_desc = desc_obj.text.split('<')[0].strip() if desc_obj is not None else ""

                # Estrazione Immagine
                image_url = ""
                enclosure = item.find("enclosure")
                if enclosure is not None and "image" in enclosure.get("type", ""):
                    image_url = enclosure.get("url")
                
                print("-> Genero Analisi...")
                new_title, body, excerpt = generate_academic_paper(title, raw_desc)
                
                new_article = {
                    "id": int(time.time()), 
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "category": cat,
                    "author": "La Redazione",
                    "title": new_title,
                    "excerpt": excerpt,
                    "body": body,
                    "imageIcon": ICONS.get(cat, "fa-newspaper"),
                    "imageReal": image_url,
                    "link": link
                }
                
                new_articles.append(new_article)
                time.sleep(3) # Pausa anti-ban

    except Exception as e:
        print(f"Errore: {e}")

# --- STEP 3: SALVA ---
if new_articles:
    updated_archive = new_articles + archive
    updated_archive = updated_archive[:50]
    json_data = json.dumps(updated_archive, indent=4)
    with open("news.js", "w", encoding="utf-8") as f:
        f.write(f"const newsData = {json_data};")
    print(f"✅ Fatto. {len(new_articles)} nuovi articoli.")
else:
    print("💤 Nessuna novità.")
