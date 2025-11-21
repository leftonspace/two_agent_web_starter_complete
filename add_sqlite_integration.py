import json
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:8000"
DB_PATH = Path("data") / "test_hr.db"


def main() -> None:
    print("Using DB:", DB_PATH.resolve())
    if not DB_PATH.exists():
        print("ERROR: DB file does not exist")
        return

    payload = {
        # NEW SCHEMA: everything lives under "config"
        "config": {
            "type": "sqlite",
            "engine": "sqlite",
            "database": str(DB_PATH.resolve()),
        }
    }

    print("\nRequest payload:")
    print(json.dumps(payload, indent=2))

    resp = requests.post(
        f"{BASE_URL}/api/integrations",
        json=payload,
        timeout=10,
    )

    print("\nStatus code:", resp.status_code)
    print("Response text:")
    print(resp.text)


if __name__ == "__main__":
    main()
