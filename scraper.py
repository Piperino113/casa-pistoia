import requests
from bs4 import BeautifulSoup
import json
import os
import time

# --- CONFIGURAZIONE ---
TELEGRAM_TOKEN = "8604946013:AAFbpWeoNX5kgiDmZYpX7m4wzySZfSIAMac"
TELEGRAM_CHAT_ID = "769829958"
FILE_VISTI = "annunci_visti.json"

# --- FILTRI ---
PREZZO_MAX = 700
LOCALI_MIN = 3

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

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

def scrapa_appag():
    url = "https://www.appag.it/appartamenti-affitto-pistoia.php"
    annunci = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("a", href=True)
        for card in cards:
            href = card["href"]
            if "affitto" in href and "sch-" in href:
                titolo_tag = card.find("h6")
                titolo = titolo_tag.text.strip() if titolo_tag else href
                prezzo_tag = card.find("h6", string=lambda t: t and "€" in t)
                prezzo_str = prezzo_tag.text.strip() if prezzo_tag else "0"
                prezzo = int("".join(filter(str.isdigit, prezzo_str.split(",")[0])))
                vani_tag = card.find_all("li")
                locali = 0
                for li in vani_tag:
                    testo = li.text.strip().lower()
                    if "vani" in testo:
                        try:
                            locali = int("".join(filter(str.isdigit, testo)))
                        except:
                            pass
                link = "https://www.appag.it/" + href if not href.startswith("http") else href
                annunci.append({
                    "titolo": titolo,
                    "prezzo": prezzo,
                    "locali": locali,
                    "link": link,
                    "fonte": "APPAG"
                })
    except Exception as e:
        invia_telegram(f"⚠️ Errore scraper APPAG: {e}")
        print(f"Errore APPAG: {e}")
    print(f"APPAG: trovati {len(annunci)} annunci")
    return annunci

def filtra(annunci):
    return [a for a in annunci if a["prezzo"] <= PREZZO_MAX and a["locali"] >= LOCALI_MIN]

def main():
    visti = carica_visti()
    tutti = scrapa_appag()
    filtrati = filtra(tutti)
    nuovi = [a for a in filtrati if a["link"] not in visti]

    print(f"Totale: {len(tutti)} | Filtrati: {len(filtrati)} | Nuovi: {len(nuovi)}")

    if not nuovi:
        print("Nessun annuncio nuovo.")
        return

    for a in nuovi:
        msg = (f"🏠 <b>{a['titolo']}</b>\n"
               f"🏢 {a['fonte']}\n"
               f"🛏 {a['locali']} vani\n"
               f"💶 {a['prezzo']}€/mese\n"
               f"🔗 {a['link']}")
        invia_telegram(msg)
        visti.append(a["link"])
        time.sleep(1)

    salva_visti(visti)
    print(f"{len(nuovi)} annunci inviati.")

if __name__ == "__main__":
    main()
