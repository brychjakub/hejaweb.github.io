#!/usr/bin/env python3
"""Update a Google Sheet with a Spendee wallet balance.

Required environment variables:
- SPENDEE_TOKEN
- SPENDEE_DEVICE_UUID
- SPENDEE_WALLET_ID
- GOOGLE_SHEET_ID
- GOOGLE_SERVICE_ACCOUNT_JSON
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SPENDEE_ENDPOINT = "https://api.spendee.com/v1.4/wallet-get-all"
SHEET_NAME = "částka na účtu"
SHEET_RANGE = f"'{SHEET_NAME}'!B1:B3"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


class SpendeeError(RuntimeError):
    """Raised when Spendee API data cannot be fetched or interpreted."""


class GoogleSheetsError(RuntimeError):
    """Raised when Google Sheets cannot be updated."""


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def load_config() -> dict[str, str]:
    """Load required configuration without printing secret values."""
    return {
        "spendee_token": _required_env("SPENDEE_TOKEN"),
        "spendee_device_uuid": _required_env("SPENDEE_DEVICE_UUID"),
        "spendee_wallet_id": _required_env("SPENDEE_WALLET_ID"),
        "google_sheet_id": _required_env("GOOGLE_SHEET_ID"),
        "google_service_account_json": _required_env("GOOGLE_SERVICE_ACCOUNT_JSON"),
    }


def parse_service_account_json(raw_value: str) -> dict[str, Any]:
    """Parse service account JSON from JSON text, a local path, or base64 JSON."""
    candidate = raw_value.strip()

    if candidate.startswith("{"):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ConfigError("GOOGLE_SERVICE_ACCOUNT_JSON contains invalid JSON.") from exc
    elif os.path.isfile(candidate):
        try:
            with open(candidate, "r", encoding="utf-8") as service_account_file:
                parsed = json.load(service_account_file)
        except OSError as exc:
            raise ConfigError("Cannot read GOOGLE_SERVICE_ACCOUNT_JSON file path.") from exc
        except json.JSONDecodeError as exc:
            raise ConfigError("GOOGLE_SERVICE_ACCOUNT_JSON file contains invalid JSON.") from exc
    else:
        try:
            decoded = base64.b64decode(candidate, validate=True).decode("utf-8")
            parsed = json.loads(decoded)
        except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ConfigError(
                "GOOGLE_SERVICE_ACCOUNT_JSON must be JSON text, a readable file path, or base64-encoded JSON."
            ) from exc

    if not isinstance(parsed, dict):
        raise ConfigError("GOOGLE_SERVICE_ACCOUNT_JSON must resolve to a JSON object.")
    return parsed


def fetch_wallets(token: str, device_uuid: str) -> list[dict[str, Any]]:
    """Fetch wallets from Spendee and validate the response shape."""
    headers = {
        "Authorization": f"Bearer {token}",
        "device-uuid": device_uuid,
        "accept": "application/json",
        "spendee-platform": "web",
        "spendee-version": "master",
    }

    try:
        response = requests.get(SPENDEE_ENDPOINT, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise SpendeeError("Could not connect to the Spendee API.") from exc

    if not response.ok:
        raise SpendeeError(f"Spendee API returned HTTP {response.status_code}.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise SpendeeError("Spendee API returned invalid JSON.") from exc

    result = payload.get("result") if isinstance(payload, dict) else None
    if not isinstance(result, list):
        raise SpendeeError("Spendee API response does not contain 'result' as an array.")

    wallets: list[dict[str, Any]] = []
    for wallet in result:
        if isinstance(wallet, dict):
            wallets.append(wallet)
    return wallets


def _wallet_identifier(wallet: dict[str, Any]) -> str | None:
    for key in ("id", "wallet_id", "uuid"):
        value = wallet.get(key)
        if value is not None:
            return str(value)
    return None


def find_wallet(wallets: list[dict[str, Any]], wallet_id: str) -> dict[str, Any]:
    """Find the requested wallet without exposing wallet data in errors."""
    for wallet in wallets:
        if _wallet_identifier(wallet) == wallet_id:
            return wallet
    raise SpendeeError("Configured Spendee wallet was not found in the API response.")


def extract_balance_and_currency(wallet: dict[str, Any]) -> tuple[Any, str]:
    """Extract balance and currency from the wallet object."""
    balance = wallet.get("balance")
    currency = wallet.get("currency")

    if isinstance(balance, dict):
        currency = currency or balance.get("currency")
        balance = balance.get("amount", balance.get("value"))

    if balance is None:
        raise SpendeeError("Selected Spendee wallet does not contain a balance.")
    if not currency:
        raise SpendeeError("Selected Spendee wallet does not contain a currency.")

    return balance, str(currency)


def build_sheets_service(service_account_info: dict[str, Any]) -> Any:
    """Create an authenticated Google Sheets API service."""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES,
        )
        return build("sheets", "v4", credentials=credentials, cache_discovery=False)
    except Exception as exc:
        raise GoogleSheetsError("Could not initialize Google Sheets credentials.") from exc


def ensure_sheet_exists(sheets_service: Any, spreadsheet_id: str, sheet_name: str) -> None:
    """Create the target sheet if it is missing."""
    try:
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing_titles = {
            sheet.get("properties", {}).get("title")
            for sheet in spreadsheet.get("sheets", [])
        }
        if sheet_name in existing_titles:
            return

        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]},
        ).execute()
    except HttpError as exc:
        raise GoogleSheetsError("Could not verify or create the target Google Sheets tab.") from exc


def update_sheet(sheets_service: Any, spreadsheet_id: str, balance: Any, currency: str) -> None:
    """Write balance, currency, and an UTC timestamp to the target range."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    values = [[balance], [currency], [timestamp]]

    try:
        ensure_sheet_exists(sheets_service, spreadsheet_id, SHEET_NAME)
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=SHEET_RANGE,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()
    except HttpError as exc:
        raise GoogleSheetsError("Could not write values to Google Sheets.") from exc


def run() -> None:
    config = load_config()
    wallets = fetch_wallets(config["spendee_token"], config["spendee_device_uuid"])
    wallet = find_wallet(wallets, config["spendee_wallet_id"])
    balance, currency = extract_balance_and_currency(wallet)
    service_account_info = parse_service_account_json(config["google_service_account_json"])
    sheets_service = build_sheets_service(service_account_info)
    update_sheet(sheets_service, config["google_sheet_id"], balance, currency)
    print(f"Updated Google Sheets tab '{SHEET_NAME}' successfully.")


def main() -> int:
    try:
        run()
    except (ConfigError, SpendeeError, GoogleSheetsError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
