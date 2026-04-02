import requests
import json
import os

# --- CONFIGURAZIONE ---
TELEGRAM_TOKEN = "8604946013:AAFbpWeoNX5kgiDmZYpX7m4wzySZfSIAMac"
TELEGRAM_CHAT_ID = "769829958"
FILE_VISTI = "annunci_visti.json"

# --- FILTRI ---
PREZZO_MAX = 700
LOCALI_MIN = 3

def carica_visti():
    if os.path.exists(FILE_VISTI):
        with open(FILE_VISTI, "r") as f:
            return json.load(f)
    return []

def salva_visti(visti):
    with open(FILE_VISTI, "w") as f:
        json.dump(visti, f)

def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": messaggio, "parse_mode": "HTML"})

def scrapa_immobiliare():
    url = "https://www.immobiliare.it/api-next/search-list/real-estates/"
    params = {
        "fkRegione": "toscana",
        "idProvincia": "PT",
        "idContratto": "2",
        "idCategoria": "1",
        "prezzoMassimo": PREZZO_MAX,
        "localiMinimo": LOCALI_MIN,
        "pag": "1",
        "paramsCount": "1",
        "from": "search_list"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    annunci = []
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        print("STATUS:", r.status_code)
        print("RISPOSTA:", r.text[:500])
        dati = r.json()
        items = dati.get("results", [])
        print(f"Annunci trovati: {len(items)}")
        for item in items:
            try:
                titolo = item.get("seo", {}).get("anchor", "")
                prezzo_info = item.get("price", {})
                prezzo = prezzo_info.get("value", 0)
                locali = item.get("properties", [{}])[0].get("rooms", 0)
                citta = item.get("properties", [{}])[0].get("location", {}).get("city", "")
                link = "https://www.immobiliare.it" + item.get("seo", {}).get("url", "")
                annunci.append({
                    "titolo": titolo,
                    "prezzo": prezzo,
                    "locali": locali,
                    "citta": citta,
                    "link": link
                })
            except:
                continue
    except Exception as e:
        invia_telegram(f"⚠️ Errore scraper Immobiliare.it: {e}")
        print(f"Errore: {e}")
    return annunci

def filtra(annunci):
    return [a for a in annunci if a["prezzo"] <= PREZZO_MAX and a["locali"] >= LOCALI_MIN]

def main():
    visti = carica_visti()
    tutti = scrapa_immobiliare()
    filtrati = filtra(tutti)
    nuovi = [a for a in filtrati if a["link"] not in visti]

    if not nuovi:
        print("Nessun annuncio nuovo.")
        return

    for a in nuovi:
        msg = (f"🏠 <b>{a['titolo']}</b>\n"
               f"📍 {a['citta']}\n"
               f"🛏 {a['locali']} locali\n"
               f"💶 {a['prezzo']}€/mese\n"
               f"🔗 {a['link']}")
        invia_telegram(msg)
        visti.append(a["link"])

    salva_visti(visti)
    print(f"{len(nuovi)} annunci inviati.")

if __name__ == "__main__":
    main()
