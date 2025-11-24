import json
import urllib.request
import xml.etree.ElementTree as ET
import html
import random
from datetime import datetime

# --- CONFIGURAZIONE FONTI (Feed RSS Reali) ---
# Usiamo ANSA per semplicità, ma potresti collegarci l'IA qui in mezzo
SOURCES = {
    "cronaca": "https://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml",
    "geopolitica": "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml",
    "tech": "https://www.ansa.it/sito/notizie/tecnologia/tecnologia_rss.xml",
    "sport": "https://www.ansa.it/sito/notizie/sport/sport_rss.xml",
    "arte": "https://www.ansa.it/sito/notizie/cultura/cultura_rss.xml"
}

# Icone per abbellire
ICONS = {
    "cronaca": "fa-user-secret",
    "geopolitica": "fa-globe-europe",
    "tech": "fa-microchip",
    "sport": "fa-running",
    "arte": "fa-film",
    "difesa": "fa-shield-alt"
}

articles_list = []

print("🤖 IL BOT SOTTOBOSCO È AL LAVORO...")

for category, url in SOURCES.items():
    try:
        print(f"   Scaricando notizie per: {category}...")
        
        # Scarica il Feed RSS
        with urllib.request.urlopen(url) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # Prende la prima notizia di ogni categoria
            item = root.find(".//item") 
            if item:
                title = item.find("title").text
                link = item.find("link").text
                desc = item.find("description").text
                
                # Pulizia base del testo (rimuove tag HTML se presenti)
                clean_desc = html.unescape(desc).split('<')[0] 

                # Aggiunge alla lista
                articles_list.append({
                    "category": category,
                    "title": title,
                    "excerpt": clean_desc[:120] + "...", # Taglia a 120 caratteri
                    "imageIcon": ICONS.get(category, "fa-newspaper"),
                    "link": link
                })
                
    except Exception as e:
        print(f"❌ Errore su {category}: {e}")

# --- AGGIUNTA MANUALE O FISSA (es. Difesa che non ha RSS facile) ---
articles_list.append({
    "category": "difesa",
    "title": "Analisi Strategica: I nuovi scenari del 2025",
    "excerpt": "Report esclusivo del Sottobosco sulle nuove tecnologie militari.",
    "imageIcon": "fa-shield-alt",
    "link": "#"
})

# --- SALVATAGGIO NEL FILE JS ---
js_content = f"const newsData = {json.dumps(articles_list, indent=4)};"

with open("news.js", "w", encoding="utf-8") as f:
    f.write(js_content)

print("\n✅ FATTO! Il file news.js è stato aggiornato con le notizie vere.")
print("👉 Ora apri index.html e vedrai le news fresche.")