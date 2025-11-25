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
    model = genai.GenerativeModel('gemini-1.5-flash') # Modello veloce ed economico

# Fonti "High Level" per professionisti
SOURCES = {
    "GEOPOLITICS": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "DEFENSE": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10", # US Defense
    "TECH & QUANTUM": "https://www.mit.edu/news/rss.xml", # MIT News
    "MARKETS": "https://www.cnbc.com/id/10000664/device/rss/rss.html" # Finance
}

# --- FUNZIONI UTILI ---
def clean_html(raw_html):
    return raw_html.split('<')[0].strip()

def get_day_of_week():
    return datetime.today().weekday() # 0 = Lunedì, 6 = Domenica

def load_existing_data():
    try:
        with open("data.js", "r", encoding="utf-8") as f:
            content = f.read().replace("const mshData = ", "").replace(";", "")
            return json.loads(content)
    except:
        return {"briefs": [], "monograph": {}}

# --- MOTORE AI ---
def generate_briefing(news_list):
    if not API_KEY: return [{"category": "SYSTEM", "text": "AI Offline."}]
    
    # Creiamo un testo unico con tutte le news per darle in pasto all'IA
    context = "\n".join([f"- {n['cat']}: {n['title']}" for n in news_list])
    
    prompt = f"""
    Sei un analista di intelligence militare per Marte Strategic Horizon.
    Leggi queste notizie grezze:
    {context}

    Compito: Estrai 5 punti chiave essenziali per un report mattutino destinato a CEO e Generali.
    Stile: Telegrafico, freddo, senza fronzoli. Solo fatti.
    Output desiderato: Una lista JSON pura (senza markdown) di oggetti con campi "category" (es. DEFENSE, MARKETS) e "text".
    Esempio: [{{"category": "DEFENSE", "text": "Nuovi movimenti truppe confine est."}}]
    """
    try:
        response = model.generate_content(prompt)
        # Pulizia brutale per assicurarsi che sia JSON valido
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Errore Briefing AI: {e}")
        return [{"category": "ERROR", "text": "Analisi dati fallita."}]

def generate_monograph(news_list):
    if not API_KEY: return None
    
    context = "\n".join([f"- {n['title']} (Source: {n['link']})" for n in news_list[:15]])
    
    prompt = f"""
    Sei un Professore Universitario di Strategia Globale. Scrivi una monografia settimanale per 'Marte Strategic Horizon'.
    
    Input Dati (Ultime notizie):
    {context}

    Compito: Scrivi un saggio approfondito (circa 800 parole) che colleghi i puntini tra queste notizie.
    Cerca pattern non ovvi tra Tecnologia, Difesa e Geopolitica.
    
    Formato Output JSON:
    {{
        "title": "Titolo Accademico in Inglese",
        "author": "Marte Intelligence Unit",
        "readTime": "5 min",
        "content": "Testo dell'articolo in HTML (usa <p>, <h3>, <strong>). Linguaggio formale, italiano.",
        "references": ["Lista delle fonti reali citate"]
    }}
    """
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Errore Monografia AI: {e}")
        return None

# --- ESECUZIONE ---
print("--- MARTE STRATEGIC HORIZON: ANALYZING ---")

# 1. Scarica News
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
            for item in tree.findall(".//item")[:4]: # Prendi 4 news per fonte
                raw_news.append({
                    "cat": cat,
                    "title": item.find("title").text,
                    "link": item.find("link").text
                })
    except:
        print(f"Fonte offline: {cat}")

# 2. Carica dati vecchi
current_data = load_existing_data()

# 3. Genera SEMPRE il Morning Brief
print("Generazione Morning Brief...")
new_briefs = generate_briefing(raw_news)
current_data["briefs"] = new_briefs

# 4. Genera MONOGRAFIA solo se è Lunedì (Day 0)
# (O se forziamo manualmente per test)
today = get_day_of_week()
if True:
    print("È Lunedì: Generazione Monografia Strategica...")
    new_mono = generate_monograph(raw_news)
    if new_mono:
        new_mono["date"] = datetime.now().strftime("%B %d, %Y")
        current_data["monograph"] = new_mono
else:
    print("Non è Lunedì: Mantengo la monografia precedente.")

# 5. Salva
json_output = json.dumps(current_data, indent=4)
with open("data.js", "w", encoding="utf-8") as f:
    f.write(f"const mshData = {json_output};")

print("--- UPDATE COMPLETE ---")

