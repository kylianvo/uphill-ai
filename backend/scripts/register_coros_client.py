"""One-off: register Uphill AI as an OAuth client with COROS (RFC 7591).

Run once per environment, then copy the printed values into backend/.env:

    python scripts/register_coros_client.py https://api.uphill-ai.io.vn/api/integrations/coros/callback

Deliberately NOT run at startup -- that would mint a new client on every deploy.
"""

import json
import os
import sys

import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.coros_oauth import REGISTRATION_URL, SCOPES  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    redirect_uri = sys.argv[1]
    response = httpx.post(
        REGISTRATION_URL,
        json={
            "client_name": "Uphill AI",
            "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "scope": SCOPES,
            "token_endpoint_auth_method": "client_secret_post",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    print(json.dumps(payload, indent=2))
    print("\nAdd to backend/.env:")
    print(f"COROS_CLIENT_ID={payload['client_id']}")
    print(f"COROS_CLIENT_SECRET={payload.get('client_secret', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
