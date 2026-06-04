#!/usr/bin/env python3
"""Update the PythonAnywhere account balance from a Spendee wallet.

Required environment variables:
- SPENDEE_DEVICE_UUID
- SPENDEE_WALLET_ID
- BACKEND_API_BASE
- BACKEND_USERNAME
- BACKEND_PASSWORD

Spendee auth can be configured in either of these ways:
- SPENDEE_TOKEN
- SPENDEE_TOKEN_URL + SPENDEE_REFRESH_TOKEN
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

    spendee_token = os.environ.get("SPENDEE_TOKEN", "").strip()
    spendee_token_url = os.environ.get("SPENDEE_TOKEN_URL", "").strip()
    spendee_refresh_token = os.environ.get("SPENDEE_REFRESH_TOKEN", "").strip()

    if not spendee_token and not (spendee_token_url and spendee_refresh_token):
        raise ConfigError(
            "Missing Spendee auth configuration: set SPENDEE_TOKEN or both "
            "SPENDEE_TOKEN_URL and SPENDEE_REFRESH_TOKEN."
        )

    return {
        "spendee_token": spendee_token,
        "spendee_token_url": spendee_token_url,
        "spendee_refresh_token": spendee_refresh_token,
        "spendee_client_id": os.environ.get("SPENDEE_CLIENT_ID", "").strip(),
        "spendee_client_secret": os.environ.get("SPENDEE_CLIENT_SECRET", "").strip(),
        "spendee_token_auth_mode": os.environ.get("SPENDEE_TOKEN_AUTH_MODE", "body").strip().lower(),
        "spendee_device_uuid": _required_env("SPENDEE_DEVICE_UUID"),
        "spendee_wallet_id": _required_env("SPENDEE_WALLET_ID"),
        "backend_api_base": backend_api_base,
        "backend_username": _required_env("BACKEND_USERNAME"),
        "backend_password": _required_env("BACKEND_PASSWORD"),
    }


def refresh_spendee_access_token(config: dict[str, str]) -> str:
    """Refresh and return a Spendee access token using an OAuth refresh token."""
    token_url = config["spendee_token_url"]
    refresh_token = config["spendee_refresh_token"]
    if not token_url or not refresh_token:
        return config["spendee_token"]

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    auth = None

    client_id = config["spendee_client_id"]
    client_secret = config["spendee_client_secret"]
    auth_mode = config["spendee_token_auth_mode"]

    if client_id and client_secret and auth_mode == "basic":
        auth = (client_id, client_secret)
    else:
        if client_id:
            data["client_id"] = client_id
        if client_secret:
            data["client_secret"] = client_secret

    headers = {
        "accept": "application/json",
        "device-uuid": config["spendee_device_uuid"],
        "spendee-platform": "web",
        "spendee-version": "master",
    }

    try:
        response = requests.post(token_url, data=data, headers=headers, auth=auth, timeout=30)
    except requests.RequestException as exc:
        raise SpendeeError("Could not connect to the Spendee token refresh endpoint.") from exc

    if not response.ok:
        raise SpendeeError(
            f"Spendee token refresh returned HTTP {response.status_code}."
            f"{_response_error_detail(response)}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise SpendeeError("Spendee token refresh returned invalid JSON.") from exc

    access_token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(access_token, str) or not access_token:
        raise SpendeeError("Spendee token refresh response does not contain an access_token.")

    return access_token


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


def _response_error_detail(response: requests.Response) -> str:
    """Return a short non-secret response detail for easier backend debugging."""
    body = response.text.strip().replace("\n", " ")
    if not body:
        return ""
    return f" Response body: {body[:300]}"


def _parse_backend_account_response(response: requests.Response, expected_amount_czk: int) -> dict[str, Any]:
    """Parse and verify that the backend confirmed the expected account balance."""
    try:
        payload = response.json()
    except ValueError as exc:
        raise BackendError("Backend account endpoint returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise BackendError("Backend account endpoint did not return a JSON object.")

    try:
        returned_amount = int(payload.get("amount_czk"))
    except (TypeError, ValueError) as exc:
        raise BackendError("Backend account endpoint did not return a valid amount_czk.") from exc

    if returned_amount != expected_amount_czk:
        raise BackendError("Backend account endpoint confirmed a different amount than requested.")

    return payload


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
        raise BackendError(
            f"Backend login returned HTTP {response.status_code}."
            f"{_response_error_detail(response)}"
        )

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


def update_backend_account(api_base: str, session_token: str, amount_czk: int) -> dict[str, Any]:
    """Update the PythonAnywhere account balance endpoint and verify the response."""
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
        raise BackendError(
            f"Backend account update returned HTTP {response.status_code}."
            f"{_response_error_detail(response)}"
        )

    payload = _parse_backend_account_response(response, amount_czk)
    if payload.get("status") != "updated":
        raise BackendError("Backend account endpoint did not confirm update status.")
    return payload


def verify_backend_account(api_base: str, session_token: str, amount_czk: int) -> dict[str, Any]:
    """Read the account endpoint after update and verify the stored value."""
    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        response = requests.get(
            f"{api_base}/account",
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise BackendError("Could not connect to the backend account verification endpoint.") from exc

    if not response.ok:
        raise BackendError(
            f"Backend account verification returned HTTP {response.status_code}."
            f"{_response_error_detail(response)}"
        )

    return _parse_backend_account_response(response, amount_czk)


def run() -> None:
    config = load_config()
    spendee_access_token = refresh_spendee_access_token(config)
    wallets = fetch_wallets(spendee_access_token, config["spendee_device_uuid"])
    wallet = find_wallet(wallets, config["spendee_wallet_id"])
    balance, currency = extract_balance_and_currency(wallet)
    validate_czk_currency(currency)
    amount_czk = to_backend_amount_czk(balance)
    session_token = login_to_backend(
        config["backend_api_base"],
        config["backend_username"],
        config["backend_password"],
    )

    print(f"Using backend API base: {config['backend_api_base']}")
    update_payload = update_backend_account(config["backend_api_base"], session_token, amount_czk)
    verify_payload = verify_backend_account(config["backend_api_base"], session_token, amount_czk)
    updated_at = verify_payload.get("updated_at") or update_payload.get("updated_at") or "unknown time"
    print(f"Updated amount_czk={amount_czk} and verified PythonAnywhere backend at {updated_at}.")


def main() -> int:
    try:
        run()
    except (ConfigError, SpendeeError, BackendError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
