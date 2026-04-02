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

def scrapa_subito():
    url = "https://api.subito.it/svc/search/v1/listings?c=1&z=10&t=a&lim=50&start=0&q=appartamento&tos=false&shp=false&ci=52&r=30"
    headers = {"User-Agent": "Mozilla/5.0"}
    annunci = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        dati = r.json()
        items = dati.get("ads", [])
        for item in items:
            try:
                titolo = item.get("subject", "")
                prezzo_info = item.get("features", {}).get("/price", {})
                prezzo = int(prezzo_info.get("values", [{}])[0].get("key", 0))
                locali_info = item.get("features", {}).get("/rooms", {})
                locali_str = locali_info.get("values", [{}])[0].get("key", "0")
                locali = int(locali_str) if locali_str.isdigit() else 0
                link = item.get("urls", {}).get("default", "")
                citta = item.get("geo", {}).get("city", {}).get("value", "")
                annunci.append({
                    "titolo": titolo,
                    "prezzo": prezzo,
                    "locali": locali,
                    "link": link,
                    "citta": citta
                })
            except:
                continue
    except Exception as e:
        invia_telegram(f"⚠️ Errore scraper Subito.it: {e}")
    return annunci

def filtra(annunci):
    return [a for a in annunci if a["prezzo"] <= PREZZO_MAX and a["locali"] >= LOCALI_MIN]

def main():
    visti = carica_visti()
    tutti = scrapa_subito()
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
