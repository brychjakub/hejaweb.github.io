# Automatická aktualizace Spendee zůstatku do Google Sheets

Script `scripts/update_spendee_google_sheet.py` načte seznam Spendee peněženek, najde peněženku podle `SPENDEE_WALLET_ID` a zapíše její zůstatek do listu `částka na účtu` v Google Sheets.

## Požadované proměnné prostředí

- `SPENDEE_TOKEN` – Bearer token pro Spendee API.
- `SPENDEE_DEVICE_UUID` – hodnota hlavičky `device-uuid`.
- `SPENDEE_WALLET_ID` – ID peněženky ve Spendee.
- `GOOGLE_SHEET_ID` – ID cílového Google Sheets dokumentu.
- `GOOGLE_SERVICE_ACCOUNT_JSON` – JSON service accountu, cesta k lokálnímu JSON souboru, nebo base64 zakódovaný JSON.

Service account musí mít přístup k cílovému Google Sheets dokumentu.

## Lokální spuštění

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-spendee.txt
export SPENDEE_TOKEN="..."
export SPENDEE_DEVICE_UUID="..."
export SPENDEE_WALLET_ID="..."
export GOOGLE_SHEET_ID="..."
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
python scripts/update_spendee_google_sheet.py
```

Alternativně lze do `GOOGLE_SERVICE_ACCOUNT_JSON` uložit cestu k lokálnímu souboru se service account JSON.

## GitHub Actions

Workflow `.github/workflows/update-spendee-sheet.yml` běží denně v 06:00 UTC a lze ho spustit ručně přes `workflow_dispatch`. Hodnoty proměnných nastavte jako repository secrets se stejnými názvy jako výše.

Script záměrně nevypisuje tokeny, service account JSON, wallet data ani jiné citlivé údaje.
