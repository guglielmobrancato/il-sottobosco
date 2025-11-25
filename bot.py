import json
import urllib.request
import xml.etree.ElementTree as ET
import ssl
import os
import time
import re
from datetime import datetime
import google.generativeai as genai

# --- 1. CONFIGURAZIONE E DEBUG CHIAVE ---
API_KEY = os.environ.get("GEMINI_API_KEY")

print("------------------------------------------------")
if API_KEY:
    masked_key = API_KEY[:5] + "..." + API_KEY[-3:]
    print(f"✅ DEBUG: Chiave trovata! ({masked_key})")
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        print("✅ DEBUG: Modello 'gemini-pro' configurato.")
    except Exception as e:
        print(f"❌ DEBUG: Errore configurazione Gemini: {e}")
else:
    print("❌ DEBUG: NESSUNA CHIAVE TROVATA.")
print("------------------------------------------------")

# --- 2. FONTI RSS ---
SOURCES = {
    "GEOPOLITICS": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "DEFENSE": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10",
    "TECH": "https://www.wired.com/feed/rss",
    "MARKETS": "https://www.cnbc.com/id/10000664/device/rss/rss.html"
}

# --- 3. FUNZIONI DI UTILITÀ ---
def load_existing_data():
    try:
        with open("data.js", "r", encoding="utf-8") as f:
            content = f.read().replace("const mshData = ", "").replace(";", "")
            return json.loads(content)
    except:
        return {"briefs": [], "monograph": {}}

def extract_json(text):
    try:
        match_array = re.search(r'\[.*\]', text, re.DOTALL)
        if match_array: return json.loads(match_array.group())
        
        match_obj = re.search(r'\{.*\}', text, re.DOTALL)
        if match_obj: return json.loads(match_obj.group())

        clean = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        print(f"⚠️ Parsing JSON fallito. Testo parziale: {text[:50]}...")
        return None

# --- 4. MOTORE AI ---
def generate_briefing(news_list):
    if not API_KEY: return [{"category": "SYSTEM", "text": "AI Offline."}]
    
    context = "\n".join([f"- {n['cat']}: {n['title']}" for n in news_list])
    prompt = f"""
    Sei un analista di intelligence. Leggi:
    {context}
    Estrai 5 punti chiave essenziali per un report strategico. Stile: Tecnico, sintetico.
    RISPONDI SOLO CON UN JSON ARRAY VALIDO:
    [
        {{"category": "DEFENSE", "text": "Sintesi notizia..."}},
        {{"category": "MARKETS", "text": "Sintesi notizia..."}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        result = extract_json(response.text)
        return result if result else [{"category": "ERROR", "text": "Dati non validi."}]
    except Exception as e:
        print(f"Errore Briefing: {e}")
        return [{"category": "ERROR", "text": "Errore API."}]

def generate_monograph(news_list):
    if not API_KEY: return None
    
    context = "\n".join([f"- {n['title']}" for n in news_list[:20]])
    prompt = f"""
    Sei un Professore di Strategia. News: {context}
    Scrivi una monografia settimanale (Titolo, Autore, Tempo lettura, Contenuto HTML, Fonti).
    Collega argomenti diversi. Usa tag HTML <p>, <h3>, <strong>.
    RISPONDI SOLO CON UN JSON VALIDO:
    {{
        "title": "Titolo Accademico",
        "author": "Marte Intelligence Unit",
        "readTime": "5 min",
        "content": "<p>Testo...</p>",
        "references": ["Fonte 1", "Fonte 2"]
    }}
    """
    try:
        response = model.generate_content(prompt)
        result = extract_json(response.text)
        return result
    except Exception as e:
        print(f"Errore Monografia: {e}")
        return None

# --- 5. ESECUZIONE ---
print("--- STARTING ANALYSIS ---")

# FIX: DEFINIZIONE VARIABILI GLOBALI PRIMA DI TUTTO
raw_news = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

# Ora possiamo avviare il loop
for cat, url in SOURCES.items():
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            for item in tree.findall(".//item")[:3]:
                title = item.find("title").text
                raw_news.append({"cat": cat, "title": title})
    except Exception as e:
        print(f"Fonte offline ({cat}): {e}")

current_data = load_existing_data()

print("Generazione Briefing...")
new_briefs = generate_briefing(raw_news)
if new_briefs:
    current_data["briefs"] = new_briefs

# FORZATURA MONOGRAFIA (if True)
if True: 
    print("Generazione Monografia (Forzata)...")
    new_mono = generate_monograph(raw_news)
    if new_mono:
        new_mono["date"] = datetime.now().strftime("%B %d, %Y")
        current_data["monograph"] = new_mono
        print("Monografia creata.")
    else:
        print("Monografia fallita.")

json_output = json.dumps(current_data, indent=4)
with open("data.js", "w", encoding="utf-8") as f:
    f.write(f"const mshData = {json_output};")

print("--- UPDATE COMPLETE ---")
