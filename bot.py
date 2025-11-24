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

# Variabile per tracciare lo stato
STATUS_MSG = "Inizializzazione..."

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        # Proviamo SOLO il modello più recente e standard
        model = genai.GenerativeModel('gemini-1.5-flash')
        STATUS_MSG = "✅ Chiave presente. Modello configurato."
    except Exception as e:
        STATUS_MSG = f"❌ Errore Configurazione: {str(e)}"
else:
    STATUS_MSG = "❌ Chiave API mancante nei Secrets di GitHub."

SOURCES = { "geopolitica": "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml" } # Solo una fonte per test veloce
ICONS = { "geopolitica": "fa-globe-europe" }

def generate_paper(title, description):
    # Se c'è stato un errore in configurazione, lo restituiamo subito
    if "❌" in STATUS_MSG:
        return title, f"DIAGNOSTICA:\n{STATUS_MSG}\n\nControlla i Secrets su GitHub.", description

    prompt = f"""
    Scrivi un'analisi accademica di 100 parole su: {title}.
    Contesto: {description}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        return title, text, "Analisi generata con successo..."
    except Exception as e:
        # SCRIVIAMO L'ERRORE ESATTO NELL'ARTICOLO
        return title, f"⚠️ ERRORE GEN: {str(e)}\n\nVersione lib: {genai.__version__}", description

# --- ESECUZIONE ---
new_articles = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': "Mozilla/5.0"}

print("--- DIAGNOSTICA SITO ---")

for cat, url in SOURCES.items():
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            # Prendiamo SOLO LA PRIMA notizia
            item = tree.find(".//item")
            if item:
                title = item.find("title").text
                desc = item.find("description").text.split('<')[0].strip()
                
                # Generazione
                new_title, body, excerpt = generate_paper(title, desc)

                new_articles.append({
                    "id": int(time.time()),
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "category": cat,
                    "author": "System Diagnostic",
                    "title": new_title,
                    "excerpt": excerpt,
                    "body": body, # Qui leggeremo l'errore
                    "imageIcon": "fa-bug",
                    "imageReal": "",
                    "link": item.find("link").text
                })
    except Exception as e:
        print(f"Errore RSS: {e}")

# SALVATAGGIO
if new_articles:
    with open("news.js", "w", encoding="utf-8") as f:
        f.write(f"const newsData = {json.dumps(new_articles, indent=4)};")
    print("✅ DATABASE DIAGNOSTICO PRONTO")
