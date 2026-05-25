import requests
import os

CUBEJS_URL = os.getenv("CUBEJS_URL", "http://localhost:4000")
CUBEJS_TOKEN = os.getenv("CUBEJS_API_SECRET", "dev-secret")

def run_cube_query(query: dict) -> list:
    response = requests.post(
        f"{CUBEJS_URL}/cubejs-api/v1/load",
        json={"query": query},
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CUBEJS_TOKEN}"
        },
        timeout=30
    )
    response.raise_for_status()
    return response.json().get("data", [])
