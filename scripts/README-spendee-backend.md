# Automatická aktualizace Spendee zůstatku do PythonAnywhere backendu

Script `scripts/update_spendee_backend.py` načte seznam Spendee peněženek, najde peněženku podle `SPENDEE_WALLET_ID` a zapíše její zůstatek do PythonAnywhere endpointu `/api/account`. Web už stav účtu načítá z backendu, takže není potřeba mezikrok přes Google Sheets.

## Požadované proměnné prostředí

- `SPENDEE_TOKEN` – samotný token pro Spendee API bez prefixu `Bearer`; fallback varianta, pokud nechcete používat refresh token.
- `SPENDEE_TOKEN_URL` – URL Spendee token endpointu, který v prohlížeči posílá `grant_type=refresh_token`.
- `SPENDEE_REFRESH_TOKEN` – refresh token ze Spendee auth response.
- `SPENDEE_CLIENT_ID` – volitelné client ID, pokud ho token endpoint vyžaduje.
- `SPENDEE_CLIENT_SECRET` – volitelný client secret, pokud ho token endpoint vyžaduje.
- `SPENDEE_TOKEN_AUTH_MODE` – volitelné; použijte `basic`, pokud endpoint vyžaduje client credentials přes HTTP Basic auth, jinak nechte prázdné.
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
export SPENDEE_TOKEN_URL="..."
export SPENDEE_REFRESH_TOKEN="..."
# export SPENDEE_CLIENT_ID="..."       # jen pokud ho token endpoint vyžaduje
# export SPENDEE_CLIENT_SECRET="..."   # jen pokud ho token endpoint vyžaduje
# export SPENDEE_TOKEN_AUTH_MODE="basic" # jen pokud endpoint vyžaduje HTTP Basic auth
export SPENDEE_DEVICE_UUID="..."
export SPENDEE_WALLET_ID="..."
export BACKEND_API_BASE="https://hejaboys.pythonanywhere.com/api"
export BACKEND_USERNAME="..."
export BACKEND_PASSWORD="..."
python scripts/update_spendee_backend.py
```

## GitHub Actions

Workflow `.github/workflows/update-spendee-backend.yml` běží denně v 06:00 UTC a lze ho spustit ručně přes `workflow_dispatch`. Hodnoty proměnných nastavte jako repository secrets se stejnými názvy jako výše.

Pro automatickou obnovu Spendee tokenu nastavte hlavně `SPENDEE_TOKEN_URL` a `SPENDEE_REFRESH_TOKEN`. `SPENDEE_TOKEN` můžete nechat jako nouzový fallback, ale při refresh flow není potřeba.

Script záměrně nevypisuje tokeny, hesla, session tokeny ani wallet data.
