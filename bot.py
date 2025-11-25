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
        # USARE GEMINI-PRO (Versione Stabile)
        model = genai.GenerativeModel('gemini-pro')
        print("✅ DEBUG: Modello 'gemini-pro' configurato.")
    except Exception as e:
        print(f"❌ DEBUG: Errore configurazione Gemini: {e}")
else:
    print("❌ DEBUG: NESSUNA CHIAVE TROVATA. Controlla i Secrets di GitHub.")
print("------------------------------------------------")

# --- 2. FONTI RSS (Aggiornate e Stabili) ---
SOURCES = {
    "GEOPOLITICS": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "DEFENSE": "https
