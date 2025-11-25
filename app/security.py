"""
This module contains security-related functions, such as webhook signature verification.
"""
import hashlib
import hmac
import os
from fastapi import Request, HTTPException
from dotenv import load_dotenv

async def verify_github_signature(request: Request):
    """
    Verifies the signature of an incoming GitHub webhook request.
    Raises an HTTPException if the signature is invalid.
    """
    load_dotenv()
    github_webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode("utf-8")
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=400, detail="X-Hub-Signature-256 header is missing.")

    body = await request.body()
    expected_signature = "sha256=" + hmac.new(github_webhook_secret, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=403, detail="Invalid signature.")

async def verify_linear_signature(request: Request):
    """
    Verifies the signature of an incoming Linear webhook request.
    Raises an HTTPException if the signature is invalid.
    """
    load_dotenv()
    linear_webhook_secret = os.getenv("LINEAR_WEBHOOK_SECRET", "").encode("utf-8")
    signature = request.headers.get("Linear-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Linear-Signature header is missing.")

    body = await request.body()
    expected_signature = hmac.new(linear_webhook_secret, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=403, detail="Invalid signature.")
