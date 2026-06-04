# Automatická aktualizace Spendee zůstatku do PythonAnywhere backendu

Script `scripts/update_spendee_backend.py` načte seznam Spendee peněženek, najde peněženku podle `SPENDEE_WALLET_ID` a zapíše její zůstatek do PythonAnywhere endpointu `/api/account`. Web už stav účtu načítá z backendu, takže není potřeba mezikrok přes Google Sheets.

## Požadované proměnné prostředí

- `SPENDEE_TOKEN` – samotný token pro Spendee API bez prefixu `Bearer`.
- `SPENDEE_DEVICE_UUID` – hodnota hlavičky `device-uuid`.
- `SPENDEE_WALLET_ID` – ID peněženky ve Spendee.
- `BACKEND_API_BASE` – base URL backend API, například `https://hejaboys.pythonanywhere.com/api`.
- `BACKEND_USERNAME` – administrátorské uživatelské jméno pro backend.
- `BACKEND_PASSWORD` – heslo administrátorského účtu pro backend.

Backend účet musí mít roli `admin`, protože endpoint `/api/account` přijímá změny jen od admina.

## Lokální spuštění

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-spendee.txt
export SPENDEE_TOKEN="..."
export SPENDEE_DEVICE_UUID="..."
export SPENDEE_WALLET_ID="..."
export BACKEND_API_BASE="https://hejaboys.pythonanywhere.com/api"
export BACKEND_USERNAME="..."
export BACKEND_PASSWORD="..."
python scripts/update_spendee_backend.py
```

## GitHub Actions

Workflow `.github/workflows/update-spendee-backend.yml` běží denně v 06:00 UTC a lze ho spustit ručně přes `workflow_dispatch`. Hodnoty proměnných nastavte jako repository secrets se stejnými názvy jako výše.

Script záměrně nevypisuje tokeny, hesla, session tokeny ani wallet data.
