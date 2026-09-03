"""
CivicSense — Server-side Authentication Utilities

Validates Supabase JWT tokens and provides a Flask decorator
to protect endpoints that require authentication.

IMPORTANT:
- Uses SUPABASE_SERVICE_ROLE_KEY (server-side only, NEVER expose to frontend)
- Derives user identity from the token, NEVER trusts frontend-provided user_id
"""

from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Any

from flask import jsonify, request

logger = logging.getLogger("civicsense.auth")

# ── Supabase Client (Service Role — backend only) ──────────

_supabase_client = None


def _get_supabase():
    """Lazily initialize the Supabase admin client."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url = os.environ.get("SUPABASE_URL", "").strip()
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    if not url or not service_key or "REPLACE_ME" in service_key:
        logger.warning(
            "Supabase credentials not configured. "
            "Auth enforcement is DISABLED. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env"
        )
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(url, service_key)
        logger.info("Supabase admin client initialized successfully.")
        return _supabase_client
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", e)
        return None


def verify_token(access_token: str) -> dict[str, Any] | None:
    """
    Validate a Supabase JWT access token and return the user object.

    Returns the user dict on success, None on failure.
    Does NOT trust any frontend-provided user_id.
    """
    sb = _get_supabase()
    if sb is None:
        return None

    try:
        result = sb.auth.get_user(access_token)
        if result and result.user:
            return {
                "id": str(result.user.id),
                "email": result.user.email,
                "email_confirmed": result.user.email_confirmed_at is not None,
            }
    except Exception as e:
        logger.warning("Token verification failed: %s", e)

    return None


def get_reporter_id(user_id: str) -> str | None:
    """
    Fetch the stable public_reporter_id (e.g. CIV-7F3A2) for a user.
    """
    sb = _get_supabase()
    if sb is None:
        return None

    try:
        result = (
            sb.table("profiles")
            .select("public_reporter_id")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if result.data:
            return result.data.get("public_reporter_id")
    except Exception as e:
        logger.warning("Failed to fetch reporter_id for user %s: %s", user_id, e)

    return None


def require_auth(f):
    """
    Flask route decorator that enforces Supabase authentication.

    Extracts the Bearer token from the Authorization header,
    validates it, and injects `auth_user_id` and `auth_reporter_id`
    as attributes on Flask's `request` object.

    If Supabase is not configured (dev mode), auth is bypassed with a warning.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        sb = _get_supabase()

        # If Supabase is not configured, allow requests through (dev mode)
        if sb is None:
            request.auth_user_id = None
            request.auth_reporter_id = None
            logger.debug("Auth bypassed (Supabase not configured)")
            return f(*args, **kwargs)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "error": "Authentication required. Please log in to submit a report."
            }), 401

        token = auth_header.split("Bearer ", 1)[1].strip()
        if not token:
            return jsonify({
                "success": False,
                "error": "Invalid authentication token."
            }), 401

        # Validate token with Supabase
        user = verify_token(token)
        if user is None:
            return jsonify({
                "success": False,
                "error": "Authentication failed. Please log in again."
            }), 401

        # Fetch the stable pseudonymous reporter ID
        reporter_id = get_reporter_id(user["id"])

        # Inject into request context
        request.auth_user_id = user["id"]
        request.auth_reporter_id = reporter_id

        return f(*args, **kwargs)

    return decorated
