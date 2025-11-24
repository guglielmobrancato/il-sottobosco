import json
import urllib.request
import xml.etree.ElementTree as ET
import ssl
import os
import time
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- CONFIGURAZIONE ---
API_KEY = os.environ.get("GEMINI_API_KEY")

# Configurazione IA con rimozione filtri di sicurezza (per notizie di guerra/cronaca)
if API_KEY:
    genai.configure(api_key=API_KEY)
    # Impostiamo tutti i filtri a BLOCK_NONE per evitare che l'IA si rifiuti di scrivere
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    model = genai.GenerativeModel('gemini-pro', safety_settings=safety_settings)

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

# --- FUNZIONE: GENERAZIONE SAGGISTICA ---
def generate_academic_paper(title, description):
    # CONTROLLO 1: Se manca la chiave, lo scriviamo nell'articolo per debug
    if not API_KEY: 
        return title, f"ERRORE SISTEMA: API KEY mancante o non letta da GitHub Secrets.\n\nDescrizione originale: {description}", description 
    
    prompt = f"""
    Agisci come Analista Senior del think-tank 'Il Sottobosco'.
    Scrivi un REPORT (250 parole) su: "{title}".
    Basati su: "{description}".
    
    Regole:
    1. Tono accademico/analitico.
    2. Inserisci un'analogia storica/filosofica.
    3. NO premesse, inizia subito col testo.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # CONTROLLO 2: Se l'IA restituisce vuoto (blocco improvviso)
        if not text or len(text) < 10:
            return title, f"L'IA ha analizzato il contenuto ma non ha generato output (Safety Block).\n\nNotizia originale: {description}", description

        # Pulizia base (se l'IA mette "Titolo:" lo togliamo)
        new_title = title
        body = text.replace("Titolo:", "").replace("**", "")
        
        # Creiamo un estratto
        excerpt = " ".join(body.split()[:30]) + "..."
        
        return new_title, body, excerpt

    except Exception as e:
        # CONTROLLO 3: Errore generico
        error_msg = f"ERRORE GENERAZIONE IA: {str(e)}\n\nTesto originale: {description}"
        return title, error_msg, description

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

# --- STEP 2: SCARICA ---
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- INIZIO SCANSIONE DEBUG ---")

for cat, url in SOURCES.items():
    try:
        print(f"📡 {cat}...", end=" ")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            
            # Prende la PRIMA notizia
            item = tree.find(".//item") 
            if item:
                link = item.find("link").text
                
                # Rimuoviamo il controllo duplicati PER ORA, per forzare la riscrittura anche se esiste già
                # if link in existing_links: ... (commentato per test)

                title = item.find("title").text
                desc_obj = item.find("description")
                raw_desc = desc_obj.text.split('<')[0].strip() if desc_obj is not None else "Dettagli non disponibili."

                image_url = ""
                enclosure = item.find("enclosure")
                if enclosure is not None and "image" in enclosure.get("type", ""):
                    image_url = enclosure.get("url")
                
                print("-> Genero...")
                new_title, body, excerpt = generate_academic_paper(title, raw_desc)
                
                new_article = {
                    "id": int(time.time()) + len(new_articles), # Hack per ID unici veloci
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
                time.sleep(4) 

    except Exception as e:
        print(f"Errore: {e}")

# --- STEP 3: SALVA (RESETTANDO TUTTO PER TEST) ---
# ATTENZIONE: Questo sovrascrive il file per eliminare le news rotte vecchie
if new_articles:
    json_data = json.dumps(new_articles, indent=4) # Salviamo SOLO le nuove
    with open("news.js", "w", encoding="utf-8") as f:
        f.write(f"const newsData = {json_data};")
    print(f"✅ Fatto. Database resettato con {len(new_articles)} news fresche.")
else:
    print("💤 Nessuna novità.")
