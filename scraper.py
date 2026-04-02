import requests
from bs4 import BeautifulSoup
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
    url = "https://www.subito.it/annunci-toscana/affitto/appartamenti/pistoia/?q=appartamento&t=a&c=1&qso=true"
    headers = {"User-Agent": "Mozilla/5.0"}
    annunci = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("div", class_="item-key-data")
        for card in cards:
            try:
                titolo = card.find("h2").text.strip()
                prezzo_tag = card.find("p", class_="price")
                prezzo_str = prezzo_tag.text.strip() if prezzo_tag else ""
                prezzo = int("".join(filter(str.isdigit, prezzo_str)))
                link_tag = card.find_parent("a")
                link = link_tag["href"] if link_tag else ""
                annunci.append({"titolo": titolo, "prezzo": prezzo, "link": link})
            except:
                continue
    except Exception as e:
        invia_telegram(f"⚠️ Errore scraper Subito.it: {e}")
    return annunci

def filtra(annunci):
    risultati = []
    for a in annunci:
        if a["prezzo"] <= PREZZO_MAX:
            risultati.append(a)
    return risultati

def main():
    visti = carica_visti()
    tutti = scrapa_subito()
    filtrati = filtra(tutti)
    nuovi = [a for a in filtrati if a["link"] not in visti]

    if not nuovi:
        print("Nessun annuncio nuovo.")
        return

    for a in nuovi:
        msg = f"🏠 <b>{a['titolo']}</b>\n💶 {a['prezzo']}€/mese\n🔗 {a['link']}"
        invia_telegram(msg)
        visti.append(a["link"])

    salva_visti(visti)
    print(f"{len(nuovi)} annunci inviati.")

if __name__ == "__main__":
    main()
