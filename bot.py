import json
import urllib.request
import xml.etree.ElementTree as ET
import ssl
import os
import time
import re
from datetime import datetime
import google.generativeai as genai
import yfinance as yf

# --- 1. CONFIGURAZIONE ---
API_KEY = os.environ.get("GEMINI_API_KEY")

print("------------------------------------------------")
if API_KEY:
    print("✅ DEBUG: Chiave API trovata.")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    print("❌ DEBUG: NESSUNA CHIAVE TROVATA.")
print("------------------------------------------------")

# --- 2. FONTI RSS (SUPER POTENZIATE & ITALIANE) ---
SOURCES = {
    # Intelligence & Difesa (Focus IT)
    "INTELLIGENCE": [
        "https://www.rid.it/feed.rss",  # Rivista Italiana Difesa
        "https://www.startmag.it/feed/", # StartMag (Geopolitica/Eco)
        "https://formiche.net/feed/"     # Formiche (Think Tank IT)
    ],
    # Scienza & Quantum
    "SCIENZA_QUANTUM": [
        "https://www.wired.it/feed/rss/topic/scienza/",
        "https://phys.org/rss-feed/",
        "https://www.lescienze.it/rss/all/rss2.0.xml"
    ],
    # Cinema (Focus IT)
    "CINEMA": [
        "https://www.cinematografo.it/rss/",
        "https://movieplayer.it/feed/news/"
    ],
    # Sanità
    "SANITA": [
        "https://www.insalutenews.it/in-salute/feed/",
        "https://www.quotidianosanita.it/rss/rss.php"
    ],
    # Geopolitica & Mercati (Mix)
    "MACRO": [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.ilsole24ore.com/rss/mondo.xml"
    ]
}

# --- 3. FUNZIONI UTILITÀ ---
def load_existing_data():
    """Carica il database esistente per non perdere l'archivio"""
    filename = "data.js"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
                # Rimuoviamo la parte JS per ottenere il JSON puro
                json_str = content.replace("const mshData = ", "").rstrip(";")
                return json.loads(json_str)
        except Exception as e:
            print(f"Errore caricamento dati esistenti: {e}")
            
    # Se fallisce o non esiste, ritorna struttura vuota
    return {
        "ticker": [], 
        "sections": [], 
        "monograph": {}, 
        "archive": []
    }

def extract_json(text):
    try:
        match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if match: return json.loads(match.group())
        clean = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return None

# --- 4. MOTORE FINANZIARIO (TICKER) ---
def get_market_data():
    print("💰 Scarico Dati Finanziari...")
    tickers = ["GC=F", "BTC-USD", "EURUSD=X", "CL=F", "^IXIC", "FTSEMIB.MI", "LDO.MI", "PLTR"]
    names = {
        "GC=F": "GOLD", "BTC-USD": "BITCOIN", "EURUSD=X": "EUR/USD", 
        "CL=F": "OIL", "^IXIC": "NASDAQ", "FTSEMIB.MI": "FTSE MIB", 
        "LDO.MI": "LEONARDO", "PLTR": "PALANTIR"
    }
    
    data = []
    try:
        stock_data = yf.download(tickers, period="2d", progress=False)['Close']
        eur_usd = stock_data["EURUSD=X"].iloc[-1]

        for sym in tickers:
            try:
                price_now = float(stock_data[sym].iloc[-1])
                price_prev = float(stock_data[sym].iloc[-2])
                change = ((price_now - price_prev) / price_prev) * 100
                
                is_usd = sym in ["GC=F", "BTC-USD", "CL=F", "^IXIC", "PLTR"]
                display_price = price_now / eur_usd if is_usd else price_now
                currency = "€"
                
                trend = "up" if change >= 0 else "down"
                arrow = "▲" if change >= 0 else "▼"
                
                data.append({
                    "name": names[sym],
                    "price": f"{currency} {display_price:,.2f}",
                    "change": f"{arrow} {abs(change):.2f}%",
                    "trend": trend
                })
            except:
                pass
    except Exception as e:
        print(f"Errore Finanza: {e}")
        data = [{"name": "MARKET DATA", "price": "OFFLINE", "change": "-", "trend": "down"}]
    
    return data

# --- 5. MOTORE AI (Multi-Sezione) ---
def analyze_sector(sector_name, news_list):
    if not API_KEY or not news_list: return None
    titles = "\n".join([f"- {n}" for n in news_list[:10]])
    prompt = f"""
    Sei un analista senior di {sector_name}.
    Leggi questi titoli recenti:
    {titles}
    
    Compito: Scrivi un BREVE report (max 3 punti elenco) su cosa succede oggi.
    Focus: Cerca sempre il coinvolgimento dell'ITALIA o implicazioni per l'Italia.
    Sezione: {sector_name}
    
    RISPONDI SOLO JSON:
    {{
        "title": "Titolo Sezione (es. Intelligence & Think Tank)",
        "items": ["Punto 1 con focus Italia...", "Punto 2...", "Punto 3..."]
    }}
    """
    try:
        response = model.generate_content(prompt)
        return extract_json(response.text)
    except:
        return None

def generate_monograph(all_news):
    if not API_KEY: return None
    context = "\n".join(all_news[:25])
    today_date = datetime.now().strftime("%d %b %Y")
    
    prompt = f"""
    Sei il Direttore di 'Marte Strategic Horizon'.
    Scrivi l'Editoriale Strategico del giorno.
    News del giorno: {context}
    
    Compito: Scrivi un articolo approfondito che colleghi Intelligence, Tecnologia e Geopolitica.
    Data di oggi: {today_date}
    
    JSON RICHIESTO:
    {{
        "title": "Titolo Strategico",
        "author": "Marte Intelligence Unit",
        "date": "{today_date}",
        "readTime": "6 min read",
        "content": "<p>Testo HTML lungo e dettagliato...</p>",
        "references": ["Fonte 1", "Fonte 2"]
    }}
    """
    try:
        response = model.generate_content(prompt)
        return extract_json(response.text)
    except:
        return None

# --- 6. ESECUZIONE & ARCHIVIAZIONE ---
print("--- STARTING MSH SYSTEM ---")

# A. Carica dati esistenti per preservare l'archivio
current_db = load_existing_data()

# B. Scarica Nuovi Dati
ticker_data = get_market_data()

# C. Scarica News RSS
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}
news_basket = {} 
all_titles_flat = []

for cat, urls in SOURCES.items():
    print(f"📡 Scansione {cat}...")
    news_basket[cat] = []
    for url in urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx) as response:
                tree = ET.fromstring(response.read())
                for item in tree.findall(".//item")[:4]:
                    t = item.find("title").text
                    news_basket[cat].append(t)
                    all_titles_flat.append(t)
        except:
            pass

# D. Genera Sezioni AI
sections_data = []
categories_map = {
    "INTELLIGENCE": "Intelligence & Think Tanks (Focus Italia)",
    "SCIENZA_QUANTUM": "Quantum Tech & Physics",
    "CINEMA": "Cinema & Cultura Italiana",
    "SANITA": "Sanità & Biotech",
    "MACRO": "Geopolitica Globale"
}
print("🧠 Analisi AI per Sezioni...")
for cat_code, cat_name in categories_map.items():
    if cat_code in news_basket:
        res = analyze_sector(cat_name, news_basket[cat_code])
        if res: sections_data.append(res)
        time.sleep(2)

# E. Genera Nuova Monografia
print("🧠 Generazione Monografia...")
new_monograph = generate_monograph(all_titles_flat)
if isinstance(new_monograph, list): new_monograph = new_monograph[0]
if isinstance(new_monograph, str): new_monograph = None

# --- F. LOGICA ARCHIVIO (CRUCIALE) ---
# 1. Recupera la monografia di "ieri" (quella che c'è attualmente nel file)
old_monograph = current_db.get("monograph", {})

# 2. Se è valida, spostala nell'archivio
if old_monograph and "title" in old_monograph and old_monograph["title"] != "Waiting for Data...":
    if "archive" not in current_db:
        current_db["archive"] = []
    
    # Inserisci in cima (indice 0)
    current_db["archive"].insert(0, old_monograph)
    
    # Mantieni solo gli ultimi 50
    current_db["archive"] = current_db["archive"][:50]
    print(f"✅ Archiviato articolo: {old_monograph['title']}")

# 3. Assembla il DB Finale
final_db = {
    "ticker": ticker_data,
    "sections": sections_data,
    "monograph": new_monograph if new_monograph else old_monograph, # Se l'AI fallisce, tieni il vecchio
    "archive": current_db.get("archive", []), # L'archivio aggiornato
    "last_update": datetime.now().strftime("%d/%m/%Y %H:%M")
}

# G. Salva su file
json_output = json.dumps(final_db, indent=4)
with open("data.js", "w", encoding="utf-8") as f:
    f.write(f"const mshData = {json_output};")

print("--- SYSTEM UPDATE COMPLETE ---")
