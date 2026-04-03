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
    url = "https://www.appag.it/immobili.php?cat=1&contratto=A"
    annunci = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("a", href=True)
        for card in cards:
            href = card["href"]
            if "sch-" in href and "affitto" in href:
                titolo_tag = card.find("h6")
                titolo = titolo_tag.text.strip() if titolo_tag else "Appartamento APPAG"
                prezzo = 0
                h6_tags = card.find_all("h6")
                for h6 in h6_tags:
                    if "€" in h6.text:
                        try:
                            prezzo = int("".join(filter(str.isdigit, h6.text.split(",")[0])))
                        except:
                            pass
                locali = 0
                for li in card.find_all("li"):
                    testo = li.text.strip().lower()
                    if "vani" in testo:
                        try:
                            locali = int("".join(filter(str.isdigit, testo)))
                        except:
                            pass
                link = "https://www.appag.it/" + href if not href.startswith("http") else href
                annunci.append({"titolo": titolo, "prezzo": prezzo, "locali": locali, "link": link, "fonte": "APPAG"})
    except Exception as e:
        invia_telegram(f"⚠️ Errore scraper APPAG: {e}")
    print(f"APPAG: trovati {len(annunci)} annunci affitto")
    return annunci

def scrapa_scrigno():
    url = "https://immobili.scrignoimmobiliare.it/it/immobili-residenziali/affitto.html"
    annunci = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("div", class_=lambda c: c and "property" in c.lower())
        if not cards:
            cards = soup.find_all("article")
        for card in cards:
            try:
                titolo_tag = card.find(["h2", "h3", "h4"])
                titolo = titolo_tag.text.strip() if titolo_tag else "Appartamento Scrigno"
                prezzo = 0
                testo_card = card.get_text()
                for parte in testo_card.split("€"):
                    if len(parte) > 0:
                        try:
                            prezzo = int("".join(filter(str.isdigit, parte.split()[0])))
                            if prezzo > 0:
                                break
                        except:
                            pass
                link_tag = card.find("a", href=True)
                link = link_tag["href"] if link_tag else ""
                if link and not link.startswith("http"):
                    link = "https://immobili.scrignoimmobiliare.it" + link
                annunci.append({"titolo": titolo, "prezzo": prezzo, "locali": 0, "link": link, "fonte": "Scrigno"})
            except:
                continue
    except Exception as e:
        invia_telegram(f"⚠️ Errore scraper Scrigno: {e}")
    print(f"Scrigno: trovati {len(annunci)} annunci affitto")
    return annunci

def filtra(annunci):
    risultati = []
    for a in annunci:
        if a["prezzo"] == 0 or a["prezzo"] <= PREZZO_MAX:
            if a["locali"] == 0 or a["locali"] >= LOCALI_MIN:
                risultati.append(a)
    return risultati

def main():
    visti = carica_visti()
    tutti = scrapa_appag() + scrapa_scrigno()
    filtrati = filtra(tutti)
    nuovi = [a for a in filtrati if a["link"] not in visti]

    print(f"Totale: {len(tutti)} | Filtrati: {len(filtrati)} | Nuovi: {len(nuovi)}")

    if not nuovi:
        print("Nessun annuncio nuovo.")
        return

    for a in nuovi:
        prezzo_str = f"{a['prezzo']}€/mese" if a["prezzo"] > 0 else "prezzo non indicato"
        locali_str = f"{a['locali']} vani" if a["locali"] > 0 else "vani non indicati"
        msg = (f"🏠 <b>{a['titolo']}</b>\n"
               f"🏢 {a['fonte']}\n"
               f"🛏 {locali_str}\n"
               f"💶 {prezzo_str}\n"
               f"🔗 {a['link']}")
        invia_telegram(msg)
        visti.append(a["link"])
        time.sleep(1)

    salva_visti(visti)
    print(f"{len(nuovi)} annunci inviati.")

if __name__ == "__main__":
    main()
