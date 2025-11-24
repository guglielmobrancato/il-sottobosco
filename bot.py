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

# --- FUNZIONE: GENERAZIONE ACCADEMICA ---
def generate_academic_paper(title, description):
    if not API_KEY: return title, description, description 
    
    prompt = f"""
    Agisci come un Ricercatore Senior del centro studi 'Il Sottobosco'.
    Scrivi un REPORT DI ANALISI (circa 300 parole) partendo da questa notizia.
    
    Linee Guida:
    1. Tono: Accademico, distaccato, analitico. Usa terminologia specifica.
    2. Obiettivo: Non fare cronaca. Analizza le cause profonde, gli impatti sociologici o geopolitici a lungo termine.
    3. Analogia: Inserisci obbligatoriamente un parallelo storico, filosofico o scientifico per contestualizzare l'evento.
    4. Struttura: Titolo saggistico -> Abstract (3 righe) -> Analisi dettagliata.
    
    Notizia Fonte: {title} - {description}
    
    Output richiesto: 
    Prima riga: Titolo Saggistico (es. "La dialettica della crisi...")
    Seconda riga: vuota
    Dalla terza riga: Il corpo del testo.
    """
    try:
        response = model.generate_content(prompt)
        full_text = response.text.strip()
        
        # Separiamo Titolo dal Corpo
        parts = full_text.split('\n', 2)
        if len(parts) >= 3:
            new_title = parts[0].replace("Titolo:", "").strip()
            body = parts[2].strip()
        else:
            new_title = title
            body = full_text

        # Creiamo un estratto (Abstract) per la home
        excerpt = " ".join(body.split()[:35]) + "..."
        
        return new_title, body, excerpt
    except:
        return title, "Analisi momentaneamente non disponibile.", "..."

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
# Header generico per non essere bloccati
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- INIZIO SCANSIONE ACCADEMICA ---")

for cat, url in SOURCES.items():
    try:
        print(f"📡 Analisi Fonte: {cat}...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            
            # Prende la prima notizia
            item = tree.find(".//item") 
            if item:
                link = item.find("link").text
                
                if link in existing_links:
                    print("   -> Già presente in archivio.")
                    continue

                title = item.find("title").text
                desc_obj = item.find("description")
                raw_desc = desc_obj.text.split('<')[0].strip() if desc_obj is not None else ""

                # --- ESTRAZIONE IMMAGINE (Nuova Feature) ---
                image_url = ""
                # Cerchiamo nel tag <enclosure> (standard RSS per le immagini)
                enclosure = item.find("enclosure")
                if enclosure is not None and "image" in enclosure.get("type", ""):
                    image_url = enclosure.get("url")
                
                print("   -> 🧠 Generazione Analisi Accademica...")
                new_title, body, excerpt = generate_academic_paper(title, raw_desc)
                
                new_article = {
                    "id": int(time.time()), 
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "category": cat,
                    "author": "La Redazione", # Autore fisso
                    "title": new_title,
                    "excerpt": excerpt,
                    "body": body,
                    "imageIcon": ICONS.get(cat, "fa-newspaper"),
                    "imageReal": image_url, # Salviamo l'URL della foto vera
                    "link": link
                }
                
                new_articles.append(new_article)
                time.sleep(4) # Pausa relax per Gemini

    except Exception as e:
        print(f"Errore su {cat}: {e}")

# --- STEP 3: SALVA ---
if new_articles:
    updated_archive = new_articles + archive
    updated_archive = updated_archive[:50]
    json_data = json.dumps(updated_archive, indent=4)
    with open("news.js", "w", encoding="utf-8") as f:
        f.write(f"const newsData = {json_data};")
    print(f"✅ Pubblicati {len(new_articles)} nuovi report di ricerca.")
else:
    print("💤 Nessun nuovo report da generare.")
