# Přihlášení do `naseAkce.html` – jak vytvořit účty

Na stránce `naseAkce.html` se přihlašuješ přes:
- **uživatelské jméno**
- **heslo**

Backend běží v `pythonanywhere/app.py` a ověřuje hesla přes hash (`werkzeug.security`).

## 1) Vytvoření prvního admin účtu

Na PythonAnywhere (v Bash konzoli) spusť:

```bash
cd ~/hejaWeb
python3 create_user.py --username tvoje_jmeno --role admin
```

Skript si bezpečně vyžádá heslo (nebude vidět na obrazovce), uloží jen hash a účet vytvoří / aktualizuje.

## 2) Vytvoření member účtu

```bash
cd ~/hejaWeb
python3 create_user.py --username nekdo --role member
```

## 3) Zobrazení existujících účtů

```bash
cd ~/hejaWeb
python3 create_user.py --list
```

Výpis ukáže `id | username | role | active` (hesla ani hashe se nevypisují).

## 4) Deaktivace účtu

```bash
cd ~/hejaWeb
python3 create_user.py --username nekdo --role member --inactive
```

## Poznámka k právům

- `member`: může **jen číst** interní akce.
- `admin`: může číst + **CRUD + zveřejňovat**.

Tohle je vynucené backendem, ne jen frontendem.

## Když nejde uložit stav účtu

Po nahrání nové verze backendu na PythonAnywhere je potřeba v administraci PythonAnywhere kliknout na **Reload** u web appky. Backend si po reloadu automaticky vytvoří tabulku `account_balance` a výchozí stav `0 Kč`.

Pokud se pořád zobrazuje chyba ukládání, zkontroluj:
- že jsi přihlášený jako účet s rolí `admin`,
- že web appka na PythonAnywhere běží na aktuální verzi `app.py`,
- že databázový soubor `/home/HejaBoys/hejaWeb/data.db` je zapisovatelný pro web appku.
