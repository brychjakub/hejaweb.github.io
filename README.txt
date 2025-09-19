https://brychjakub.github.io/hejaweb.github.io/index.html

Pro lokální vývoj je potřeba:
- python

pak dát podle verze pythonu ve složce, kde je index.html:
python -m http.server 8000
(já mám python 3 tak musim použít python3 -m http.server 8000)

pak to bude na localhostu:
1. http://0.0.0.0:8000/

---
Google Analytics:
- Nastavte Measurement ID v souboru assets/ga.json (klíč "measurementId").
- Případně lze přidat do <head> meta tag: <meta name="ga-measurement-id" content="G-XXXXXXXXXX">. Meta má přednost.
- Není potřeba upravovat jednotlivé stránky – skript se načítá automaticky přes assets/js/footer.js.

