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

# --- 5. MOTORE AI (Con Hyperlink e Tono Accademico) ---

def analyze_sector(sector_name, news_list):
    """Analizza una singola sezione laterale"""
    if not API_KEY or not news_list: return None
    
    # news_list ora è una lista di stringhe formattate "TITOLO | URL"
    # Per la sidebar, passiamo solo i titoli per brevità, o i primi 5 con URL
    formatted_news = "\n".join(news_list[:8])
    
    prompt = f"""
    Sei un analista senior di {sector_name} presso un think tank strategico.
    Ecco le notizie agenzia (Titolo | URL):
    {formatted_news}
    
    Compito: Sintetizza 3 punti chiave essenziali.
    Stile: Telegrafico, Intelligence, Focus Italia.
    
    RISPONDI SOLO JSON:
    {{
        "title": "Titolo Sezione (es. Intelligence & Think Tank)",
        "items": ["Punto 1...", "Punto 2...", "Punto 3..."]
    }}
    """
    try:
        response = model.generate_content(prompt)
        return extract_json(response.text)
    except:
        return None

def generate_monograph_academic(all_news_with_links):
    """Genera l'articolo principale con stile accademico e hyperlink"""
    if not API_KEY: return None
    
    # Prendiamo le prime 30 notizie con i link
    context = "\n".join(all_news_with_links[:30])
    today_date = datetime.now().strftime("%d %b %Y")
    
    prompt = f"""
    Sei un Ricercatore Universitario e Analista Strategico. Stai scrivendo un paper per "Marte Strategic Horizon".
    
    FONTI DISPONIBILI (Usa queste URL per le citazioni):
    {context}
    
    ISTRUZIONI RIGIDE:
    1.  **Tono:** Accademico, formale, distaccato, analitico. Evita aggettivi sensazionalistici. Usa termini tecnici appropriati.
    2.  **Contenuto:** Approfondisci il contesto storico e le implicazioni tecniche/geopolitiche a lungo termine. Collega i puntini tra eventi apparentemente distanti.
    3.  **Veridicità e Hyperlink (FONDAMENTALE):** - Ogni volta che citi un fatto specifico derivato dalle fonti, DEVI inserire un hyperlink HTML su una parola chiave pertinente.
        - Esempio: "Il recente <a href='https://...'>accordo bilaterale</a> suggerisce..."
        - Usa SOLO le URL fornite nella lista sopra. Non inventare link.
    4.  **Struttura:** - Introduzione (Abstract)
        - Analisi del Contesto Storico
        - Sviluppi Tecnici/Strategici
        - Conclusioni Prospettiche
        - Bibliografia (Lista puntata semplice delle fonti usate)

    Data di oggi: {today_date}
    
    RISPONDI SOLO JSON COMPATIBILE:
    {{
        "title": "Titolo Accademico e Complesso",
        "author": "Marte Research Dept.",
        "date": "{today_date}",
        "readTime": "12 min read",
        "content": "HTML body dell'articolo con paragrafi <p>, titoli <h3> e hyperlink <a href>...",
        "references": ["Fonte 1", "Fonte 2"]
    }}
    """
    try:
        response = model.generate_content(prompt)
        return extract_json(response.text)
    except Exception as e:
        print(f"Errore generazione monografia: {e}")
        return None

# --- 6. ESECUZIONE & ARCHIVIAZIONE ---
print("--- STARTING MSH SYSTEM (ACADEMIC MODE) ---")

# A. Carica dati esistenti
current_db = load_existing_data()

# B. Scarica Nuovi Dati Finanziari
ticker_data = get_market_data()

# C. Scarica News RSS (CON I LINK)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

news_basket_for_sections = {} 
all_news_with_links = [] # Lista formattata "TITOLO | URL" per la monografia

for cat, urls in SOURCES.items():
    print(f"📡 Scansione {cat}...")
    news_basket_for_sections[cat] = []
    
    for url in urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx) as response:
                tree = ET.fromstring(response.read())
                for item in tree.findall(".//item")[:5]: # Prendiamo i primi 5 per feed
                    t = item.find("title").text
                    
                    # Tentativo di estrarre il link (alcuni RSS usano namespace, proviamo standard)
                    l = item.find("link").text if item.find("link") is not None else ""
                    # Se il link è vuoto, proviamo a cercarlo come attributo o pulirlo
                    if not l: l = "https://marte-strategic-horizon.com" # Fallback
                    
                    # Pulizia stringhe
                    t = t.strip()
                    l = l.strip()
                    
                    # Salvataggio
                    entry_str = f"TITOLO: {t} | URL: {l}"
                    news_basket_for_sections[cat].append(entry_str)
                    all_news_with_links.append(entry_str)
        except Exception as e:
            print(f"Errore lettura feed {url}: {e}")

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
    if cat_code in news_basket_for_sections:
        res = analyze_sector(cat_name, news_basket_for_sections[cat_code])
        if res: sections_data.append(res)
        time.sleep(2)

# E. Genera Nuova Monografia Accademica
print("🧠 Generazione Monografia Accademica...")
new_monograph = generate_monograph_academic(all_news_with_links)

# Validazione risultato AI
if isinstance(new_monograph, list): new_monograph = new_monograph[0]
if isinstance(new_monograph, str): new_monograph = None

# --- F. LOGICA ARCHIVIO ---
old_monograph = current_db.get("monograph", {})

# Archivia solo se c'è un articolo valido
if old_monograph and "title" in old_monograph and old_monograph["title"] != "Waiting for Data...":
    if "archive" not in current_db:
        current_db["archive"] = []
    current_db["archive"].insert(0, old_monograph)
    current_db["archive"] = current_db["archive"][:50]
    print(f"✅ Archiviato articolo: {old_monograph['title']}")

# G. Assembla il DB Finale
final_db = {
    "ticker": ticker_data,
    "sections": sections_data,
    "monograph": new_monograph if new_monograph else old_monograph, # Se AI fallisce, mantieni vecchio
    "archive": current_db.get("archive", []),
    "last_update": datetime.now().strftime("%d/%m/%Y %H:%M")
}

# H. Salva su file
json_output = json.dumps(final_db, indent=4)
with open("data.js", "w", encoding="utf-8") as f:
    f.write(f"const mshData = {json_output};")

print("--- SYSTEM UPDATE COMPLETE ---")
