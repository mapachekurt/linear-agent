import httpx
import os
from dotenv import load_dotenv

def get_linear_client() -> httpx.AsyncClient:
    """Returns an authenticated httpx client for the Linear API."""
    load_dotenv()
    linear_api_key = os.getenv("LINEAR_API_KEY")
    if not linear_api_key:
        raise ValueError("LINEAR_API_KEY must be set.")

    return httpx.AsyncClient(
        base_url="https://api.linear.app/graphql",
        headers={
            "Authorization": f"Bearer {linear_api_key}",
            "Content-Type": "application/json",
        },
    )
