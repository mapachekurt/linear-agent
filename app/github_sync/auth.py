import jwt
import time
from typing import Optional
import httpx
import os
from dotenv import load_dotenv

def get_jwt() -> str:
    """Creates a JWT for GitHub App authentication."""
    load_dotenv()
    github_app_id = os.getenv("GITHUB_APP_ID")
    github_private_key = os.getenv("GITHUB_PRIVATE_KEY")

    if not github_app_id or not github_private_key:
        raise ValueError("GitHub App ID and Private Key must be set.")

    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),
        "iss": github_app_id
    }
    return jwt.encode(payload, github_private_key, algorithm="RS256")

async def get_installation_access_token() -> Optional[str]:
    """Gets an installation access token for the GitHub App."""
    load_dotenv()
    github_installation_id = os.getenv("GITHUB_INSTALLATION_ID")

    if not github_installation_id:
        raise ValueError("GitHub Installation ID must be set.")

    jwt_token = get_jwt()
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/app/installations/{github_installation_id}/access_tokens"

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)

    if response.status_code == 201:
        return response.json()["token"]
    else:
        # Log the error or handle it as needed
        print(f"Error getting installation access token: {response.text}")
        return None
