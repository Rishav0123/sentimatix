import os
import logging
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# Loaded from Railway environment variables
RAPIDAPI_PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET")

# Maps RapidAPI plan names → Sentimatix tier strings
PLAN_TIER_MAP = {
    "BASIC": "free",
    "PRO": "pro",
    "ULTRA": "enterprise",
    "MEGA": "enterprise",
}

# RapidAPI rate limits per day (slightly less than direct portal)
RAPIDAPI_RATE_LIMITS = {
    "free": 30,
    "pro": 500,
    "enterprise": 5000,
}


def is_rapidapi_request(request: Request) -> bool:
    """Returns True if the request originated from RapidAPI's proxy."""
    return "x-rapidapi-proxy-secret" in request.headers


def get_rapidapi_tier(request: Request) -> str | None:
    """
    Validates the RapidAPI proxy secret and returns the Sentimatix tier
    based on the subscriber's plan. Returns None if request is not from RapidAPI.

    Raises 403 if the proxy secret is present but invalid (spoofing attempt).
    """
    secret = request.headers.get("x-rapidapi-proxy-secret")

    # Not a RapidAPI request — fall through to Supabase auth
    if not secret:
        return None

    # Proxy secret is present but env var is not configured — log and reject
    if not RAPIDAPI_PROXY_SECRET:
        logger.error("RAPIDAPI_PROXY_SECRET env var is not set but a RapidAPI request was received.")
        raise HTTPException(
            status_code=500,
            detail="API provider configuration error. Please contact support."
        )

    # Reject spoofed requests (someone calling Railway directly with a fake secret)
    if secret != RAPIDAPI_PROXY_SECRET:
        logger.warning(
            f"Rejected request with invalid RapidAPI proxy secret. "
            f"Source IP: {request.client.host if request.client else 'unknown'}"
        )
        raise HTTPException(status_code=403, detail="Forbidden: Invalid proxy secret.")

    # Map the RapidAPI subscription plan to a Sentimatix tier
    plan = request.headers.get("x-rapidapi-subscription", "BASIC").upper()
    tier = PLAN_TIER_MAP.get(plan, "free")

    rapidapi_user = request.headers.get("x-rapidapi-user", "unknown")
    logger.info(f"RapidAPI request authenticated: user={rapidapi_user}, plan={plan}, tier={tier}")

    return tier
