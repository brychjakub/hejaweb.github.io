#!/usr/bin/env python3
"""Update the PythonAnywhere account balance from a Spendee wallet.

Required environment variables:
- SPENDEE_TOKEN
- SPENDEE_DEVICE_UUID
- SPENDEE_WALLET_ID
- BACKEND_API_BASE
- BACKEND_USERNAME
- BACKEND_PASSWORD
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

import requests

SPENDEE_ENDPOINT = "https://api.spendee.com/v1.4/wallet-get-all"


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


class SpendeeError(RuntimeError):
    """Raised when Spendee API data cannot be fetched or interpreted."""


class BackendError(RuntimeError):
    """Raised when the PythonAnywhere backend cannot be updated."""


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def load_config() -> dict[str, str]:
    """Load required configuration without printing secret values."""
    backend_api_base = _required_env("BACKEND_API_BASE").rstrip("/")

    return {
        "spendee_token": _required_env("SPENDEE_TOKEN"),
        "spendee_device_uuid": _required_env("SPENDEE_DEVICE_UUID"),
        "spendee_wallet_id": _required_env("SPENDEE_WALLET_ID"),
        "backend_api_base": backend_api_base,
        "backend_username": _required_env("BACKEND_USERNAME"),
        "backend_password": _required_env("BACKEND_PASSWORD"),
    }


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

    return [wallet for wallet in result if isinstance(wallet, dict)]


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


def extract_balance_and_currency(wallet: dict[str, Any]) -> tuple[Decimal, str]:
    """Extract the wallet balance and currency."""
    balance = wallet.get("balance")
    currency = wallet.get("currency")

    if isinstance(balance, dict):
        currency = currency or balance.get("currency")
        balance = balance.get("amount", balance.get("value"))

    if balance is None:
        raise SpendeeError("Selected Spendee wallet does not contain a balance.")
    if not currency:
        raise SpendeeError("Selected Spendee wallet does not contain a currency.")

    try:
        parsed_balance = Decimal(str(balance))
    except (InvalidOperation, ValueError) as exc:
        raise SpendeeError("Selected Spendee wallet balance is not a valid number.") from exc

    return parsed_balance, str(currency).upper()


def validate_czk_currency(currency: str) -> None:
    """Ensure the selected wallet is in CZK before writing to amount_czk."""
    if currency != "CZK":
        raise SpendeeError("Selected Spendee wallet currency is not CZK.")


def to_backend_amount_czk(balance: Decimal) -> int:
    """Convert the Spendee balance to the integer CZK value expected by the backend."""
    return int(balance.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def login_to_backend(api_base: str, username: str, password: str) -> str:
    """Login to PythonAnywhere and return an API session token."""
    try:
        response = requests.post(
            f"{api_base}/auth/login",
            json={"username": username, "password": password},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise BackendError("Could not connect to the backend login endpoint.") from exc

    if not response.ok:
        raise BackendError(f"Backend login returned HTTP {response.status_code}.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise BackendError("Backend login returned invalid JSON.") from exc

    token = payload.get("token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token:
        raise BackendError("Backend login response does not contain a session token.")

    user = payload.get("user")
    role = user.get("role") if isinstance(user, dict) else None
    if role != "admin":
        raise BackendError("Backend login user is not an admin.")

    return token


def update_backend_account(api_base: str, session_token: str, amount_czk: int) -> None:
    """Update the PythonAnywhere account balance endpoint."""
    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        response = requests.put(
            f"{api_base}/account",
            headers=headers,
            json={"amount_czk": amount_czk},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise BackendError("Could not connect to the backend account endpoint.") from exc

    if not response.ok:
        raise BackendError(f"Backend account update returned HTTP {response.status_code}.")


def run() -> None:
    config = load_config()
    wallets = fetch_wallets(config["spendee_token"], config["spendee_device_uuid"])
    wallet = find_wallet(wallets, config["spendee_wallet_id"])
    balance, currency = extract_balance_and_currency(wallet)
    validate_czk_currency(currency)
    amount_czk = to_backend_amount_czk(balance)
    session_token = login_to_backend(
        config["backend_api_base"],
        config["backend_username"],
        config["backend_password"],
    )
    update_backend_account(config["backend_api_base"], session_token, amount_czk)
    print("Updated PythonAnywhere account balance successfully.")


def main() -> int:
    try:
        run()
    except (ConfigError, SpendeeError, BackendError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
