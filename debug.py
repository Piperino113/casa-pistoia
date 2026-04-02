import requests

url = "https://www.subito.it/annunci-toscana/affitto/appartamenti/pistoia/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

r = requests.get(url, headers=headers, timeout=10)
print("STATUS:", r.status_code)
print("LUNGHEZZA HTML:", len(r.text))
print("PRIMI 2000 CARATTERI:")
print(r.text[:2000])
```

4. **Commit changes** → **Commit changes**

Poi su GitHub vai nel file `Procfile`, clicca la matita e cambia il contenuto in:
```
worker: python debug.py
