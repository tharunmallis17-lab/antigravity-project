"""
CivicRoute AI - Backend Server
Intelligent Citizen Complaint Routing & Department Grievance Management System
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

import departments
import data_store
import auth

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "civicroute_super_secret_hackathon_2026")
CORS(app)

# Ensure data directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "templates"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "static"), exist_ok=True)


# ==============================================================================
# VIEW ROUTES
# ==============================================================================

@app.route("/")
def index():
    """Serves the main application page."""
    return render_template("index.html")


# ==============================================================================
# AUTHENTICATION API
# ==============================================================================

@app.route("/api/auth/google", methods=["POST"])
def google_auth():
    """
    Authenticates a citizen using Google Sign-In.
    Accepts client-side user object (or Firebase ID token).
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    name = data.get("name", "Citizen").strip()
    uid = data.get("uid") or f"google_{email.replace('@', '_').replace('.', '_')}"
    photo_url = data.get("photoURL", "")
    
    if not email:
        return jsonify({"error": "Valid email address is required for Google Sign-In."}), 400
        
    # Register/update user profile in data store
    user_record = {
        "uid": uid,
        "email": email,
        "name": name,
        "photoURL": photo_url,
        "phone": data.get("phone", ""),
        "preferredLanguage": data.get("preferredLanguage", "English / Tamil"),
        "defaultLocation": data.get("defaultLocation", "Dharmapuri, Tamil Nadu"),
    }
    user = data_store.upsert_user(user_record)
    
    # Generate signed session token
    token = auth.generate_token({"uid": user["uid"], "email": user["email"], "role": user["role"]})
    session["token"] = token
    
    return jsonify({
        "success": True,
        "token": token,
        "user": user,
        "message": "Signed in successfully with Google."
    })


@app.route("/api/auth/admin-login", methods=["POST"])
def admin_login():
    """
    Authenticates a department admin.
    Strictly verifies @gov.in domain and pre-approved department mapping.
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    
    if not email:
        return jsonify({"error": "Admin email is required."}), 400
        
    # 1. Enforce @gov.in domain requirement
    if not email.endswith("@gov.in"):
        return jsonify({
            "error": "Access Denied: Department Admin login requires an official @gov.in email address."
        }), 403
        
    # 2. Enforce pre-approved government directory mapping
    department = departments.get_department_for_admin(email)
    if not department:
        return jsonify({
            "error": f"Access Denied: Account '{email}' is not registered with any approved government department."
        }), 403
        
    # 3. Verify password (default demo password or configured password)
    if password != departments.DEFAULT_ADMIN_PASSWORD:
        return jsonify({"error": "Invalid administrative credentials."}), 401
        
    # Create / update admin profile
    admin_uid = f"admin_{email.replace('@', '_').replace('.', '_')}"
    admin_user = data_store.upsert_user({
        "uid": admin_uid,
        "email": email,
        "name": email.split(".")[0].upper() + " Admin",
        "department": department,
        "role": "admin"
    })
    
    # Generate signed token
    token = auth.generate_token({
        "uid": admin_user["uid"],
        "email": admin_user["email"],
        "role": "admin",
        "department": department
    })
    session["token"] = token
    
    return jsonify({
        "success": True,
        "token": token,
        "user": admin_user,
        "department": department,
        "message": f"Authenticated as {department} Administrator."
    })


@app.route("/api/auth/me", methods=["GET"])
def get_current_session_user():
    """Returns currently authenticated user profile and role details."""
    user = auth.get_current_user_from_request()
    if not user:
        return jsonify({"authenticated": False, "user": None}), 200
        
    response_data = {
        "authenticated": True,
        "user": user
    }
    if user.get("role") == "admin":
        response_data["department"] = departments.get_department_for_admin(user.get("email"))
        response_data["dailyQuota"] = data_store.get_admin_daily_processed(user.get("email"))
        
    return jsonify(response_data)


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    """Clears user session."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})


# ==============================================================================
# PROFILE API
# ==============================================================================

@app.route("/api/profile", methods=["GET", "POST"])
@auth.citizen_required
def profile_endpoint(current_user):
    """Retrieves or updates permitted profile fields."""
    if request.method == "GET":
        return jsonify({"success": True, "user": current_user})
        
    data = request.get_json() or {}
    # Email is non-editable
    updated_fields = {
        "uid": current_user["uid"],
        "email": current_user["email"],
        "name": data.get("name", current_user.get("name")),
        "phone": data.get("phone", current_user.get("phone")),
        "preferredLanguage": data.get("preferredLanguage", current_user.get("preferredLanguage")),
        "defaultLocation": data.get("defaultLocation", current_user.get("defaultLocation")),
    }
    user = data_store.upsert_user(updated_fields)
    return jsonify({"success": True, "user": user, "message": "Profile updated successfully."})


# ==============================================================================
# SECURITY VERIFICATION ROUTE (TESTING)
# ==============================================================================

@app.route("/api/admin/verify", methods=["GET"])
@auth.admin_required
def admin_verify(current_user, department):
    """Protected test route to verify server-side admin role enforcement."""
    return jsonify({
        "authorized": True,
        "email": current_user.get("email"),
        "department": department,
        "dailyQuota": data_store.get_admin_daily_processed(current_user.get("email"))
    })


# ==============================================================================
# DIRECTORY / CONFIG METADATA
# ==============================================================================

@app.route("/api/config/departments", methods=["GET"])
def get_departments_config():
    """Provides controlled mapping and approved admin list for demo UI."""
    return jsonify({
        "categories": departments.CATEGORY_DEPARTMENT_MAP,
        "approvedAdmins": departments.get_all_approved_admins(),
        "slaStandards": departments.SLA_DAYS_BY_PRIORITY,
        "defaultLimit": departments.DEFAULT_DAILY_PROCESSING_LIMIT
    })


# ==============================================================================
# SEED DATABASE ON STARTUP IF EMPTY
# ==============================================================================

with app.app_context():
    db = data_store._load_db()
    if not db["complaints"]:
        import seed_data
        seed_data.seed_database()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
