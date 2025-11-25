import json
import urllib.request
import xml.etree.ElementTree as ET
import ssl
import os
import time
from datetime import datetime
import google.generativeai as genai

# --- DEBUG CHIAVE API ---
API_KEY = os.environ.get("GEMINI_API_KEY")

print("------------------------------------------------")
if API_KEY:
    masked_key = API_KEY[:5] + "..." + API_KEY[-3:]
    print(f"✅ DEBUG: Chiave trovata! ({masked_key})")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("❌ DEBUG: NESSUNA CHIAVE TROVATA. Variabile ambiente vuota.")
print("------------------------------------------------")

# Fonti "High Level"
SOURCES = {
    "GEOPOLITICS": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "DEFENSE": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10",
    "TECH & QUANTUM": "https://www.mit.edu/news/rss.xml",
    "MARKETS": "https://www.cnbc.com/id/10000664/device/rss/rss.html"
}

# --- FUNZIONI ---
def get_day_of_week():
    return datetime.today().weekday()

def load_existing_data():
    try:
        with open("data.js", "r", encoding="utf-8") as f:
            content = f.read().replace("const mshData = ", "").replace(";", "")
            return json.loads(content)
    except:
        return {"briefs": [], "monograph": {}}

# --- IA GENERATION ---
def generate_briefing(news_list):
    if not API_KEY: return [{"category": "SYSTEM", "text": "AI Offline (No Key)."}]
    
    context = "\n".join([f"- {n['cat']}: {n['title']}" for n in news_list])
    prompt = f"""
    Sei un analista militare. Leggi:
    {context}
    Estrai 5 punti chiave essenziali per un report mattutino (CEO/Generali).
    Output JSON puro: [{{"category": "CAT", "text": "Sintesi notizia"}}]
    """
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Errore Brief: {e}")
        return [{"category": "ERROR", "text": "Analisi fallita."}]

def generate_monograph(news_list):
    if not API_KEY: return None
    
    context = "\n".join([f"- {n['title']}" for n in news_list[:15]])
    prompt = f"""
    Sei un Professore di Strategia. Scrivi una monografia settimanale (800 parole).
    News: {context}
    Output JSON:
    {{
        "title": "Titolo Accademico",
        "author": "Marte Intelligence Unit",
        "readTime": "5 min",
        "content": "Testo HTML formale.",
        "references": ["Fonte 1", "Fonte 2"]
    }}
    """
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Errore Monografia: {e}")
        return None

# --- ESECUZIONE ---
print("--- STARTING ANALYSIS ---")

raw_news = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

for cat, url in SOURCES.items():
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as response:
            tree = ET.fromstring(response.read())
            for item in tree.findall(".//item")[:3]:
                raw_news.append({"cat": cat, "title": item.find("title").text})
    except:
        print(f"Fonte offline: {cat}")

current_data = load_existing_data()

# Genera Brief
new_briefs = generate_briefing(raw_news)
current_data["briefs"] = new_briefs

# Genera Monografia (FORZATA PER OGGI: if True)
if True: 
    print("Forcing Monograph Generation...")
    new_mono = generate_monograph(raw_news)
    if new_mono:
        new_mono["date"] = datetime.now().strftime("%B %d, %Y")
        current_data["monograph"] = new_mono

# Salva
json_output = json.dumps(current_data, indent=4)
with open("data.js", "w", encoding="utf-8") as f:
    f.write(f"const mshData = {json_output};")

print("--- DONE ---")






