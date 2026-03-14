"""API Key authentication middleware."""

from fastapi import HTTPException, Request

from api.config import settings


def verify_api_key(api_key: str) -> bool:
    """
    Verify if the provided API key is valid.

    Args:
        api_key: The API key to verify

    Returns:
        True if valid, False otherwise
    """
    if not settings.valid_api_keys:
        # No API keys configured - allow all requests
        return True

    return api_key in settings.valid_api_keys


def require_api_key(request: Request) -> None:
    """
    Validate API key from request headers.

    Args:
        request: FastAPI request object

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # Skip auth if no API keys are configured
    if not settings.valid_api_keys:
        return

    # Get API key from header
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header.",
        )

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )
