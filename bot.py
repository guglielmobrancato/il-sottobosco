import json
import urllib.request
import xml.etree.ElementTree as ET
import html
import ssl

# --- CONFIGURAZIONE ---
SOURCES = {
    "cronaca": "https://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml",
    "geopolitica": "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml",
    "tech": "https://www.ansa.it/sito/notizie/tecnologia/tecnologia_rss.xml",
    "sport": "https://www.ansa.it/sito/notizie/sport/sport_rss.xml",
    "arte": "https://www.ansa.it/sito/notizie/cultura/cultura_rss.xml"
}

ICONS = {
    "cronaca": "fa-user-secret",
    "geopolitica": "fa-globe-europe",
    "tech": "fa-microchip",
    "sport": "fa-running",
    "arte": "fa-film",
    "difesa": "fa-shield-alt"
}

# Fix per problemi di certificati SSL su alcuni server
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Header per fingere di essere un browser reale (evita il blocco 403)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

articles_list = []

print("🤖 IL BOT 2.0 STA LAVORANDO...")

for category, url in SOURCES.items():
    try:
        print(f"   📡 Scaricando: {category}...")
        
        # Creiamo la richiesta con il "biglietto da visita" (User-Agent)
        req = urllib.request.Request(url, headers=HEADERS)
        
        with urllib.request.urlopen(req, context=ctx) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # Prende i primi 2 articoli per ogni categoria (così riempiamo bene il sito)
            for item in root.findall(".//item")[:2]:
                title = item.find("title").text
                link = item.find("link").text
                desc = item.find("description").text
                
                # Pulizia descrizione
                if desc:
                    clean_desc = html.unescape(desc).split('<')[0].strip()
                else:
                    clean_desc = "Leggi l'articolo completo sul sito."

                articles_list.append({
                    "category": category,
                    "title": title,
                    "excerpt": clean_desc[:110] + "...",
                    "imageIcon": ICONS.get(category, "fa-newspaper"),
                    "link": link
                })
                
    except Exception as e:
        print(f"❌ Errore critico su {category}: {e}")

# --- AGGIUNTA MANUALE ---
articles_list.append({
    "category": "difesa",
    "title": "Analisi Strategica: Scenari 2025",
    "excerpt": "Report esclusivo del Sottobosco sulle nuove tecnologie militari e l'impatto globale.",
    "imageIcon": "fa-shield-alt",
    "link": "https://www.rid.it/"
})

# --- SALVATAGGIO ---
# Se abbiamo scaricato qualcosa, scriviamo il file.
if len(articles_list) > 1:
    js_content = f"const newsData = {json.dumps(articles_list, indent=4)};"
    with open("news.js", "w", encoding="utf-8") as f:
        f.write(js_content)
    print("\n✅ FILE SCRITTO CORRETTAMENTE!")
else:
    print("\n⚠️ ATTENZIONE: Non ho trovato news. Il file non è stato toccato.")
