"""
Authentication & Role-Based Authorization Module for CivicRoute AI
Implements strict server-side authorization for Citizens and Department Admins.
"""

import os
import hmac
import hashlib
import json
import base64
from functools import wraps
from flask import request, jsonify, session
from departments import (
    ADMIN_DEPARTMENT_MAP,
    DEFAULT_ADMIN_PASSWORD,
    get_department_for_admin,
    is_valid_admin_email,
)
import data_store

SECRET_KEY = os.getenv("SECRET_KEY", "civicroute_secret_hackathon_key_2026")


def generate_token(payload: dict) -> str:
    """Generates a secure HMAC-signed base64 token."""
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    combined = {
        "payload": payload,
        "sig": signature
    }
    return base64.urlsafe_b64encode(json.dumps(combined).encode("utf-8")).decode("utf-8")


def verify_token(token_str: str) -> dict | None:
    """Verifies HMAC signature and returns payload if valid."""
    try:
        raw_json = base64.urlsafe_b64decode(token_str.encode("utf-8")).decode("utf-8")
        data = json.loads(raw_json)
        payload = data.get("payload")
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), json.dumps(payload, sort_keys=True).encode("utf-8"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(data.get("sig", ""), expected_sig):
            return payload
    except Exception:
        pass
    return None


def get_current_user_from_request() -> dict | None:
    """Extracts user from Authorization Bearer header or Flask session."""
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "token" in session:
        token = session["token"]
        
    if not token:
        return None
        
    payload = verify_token(token)
    if not payload or "uid" not in payload:
        return None
        
    # Refresh from persistent store
    user = data_store.get_user_by_uid(payload["uid"])
    return user


# ==============================================================================
# AUTHORIZATION DECORATORS
# ==============================================================================

def citizen_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user_from_request()
        if not user:
            return jsonify({"error": "Authentication required. Please sign in."}), 401
        return f(user, *args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user_from_request()
        if not user:
            return jsonify({"error": "Admin authentication required. Please sign in with your @gov.in credentials."}), 401
            
        if user.get("role") != "admin":
            return jsonify({"error": "Access Forbidden: Admin privileges required."}), 403
            
        admin_email = user.get("email", "").strip().lower()
        dept = get_department_for_admin(admin_email)
        if not dept:
            return jsonify({"error": "Access Forbidden: Account is not associated with an approved government department."}), 403
            
        return f(user, dept, *args, **kwargs)
    return decorated
