"""
Data Access Layer for CivicRoute AI
Provides persistent storage for users, complaints, notifications, and admin processing quotas.
Automatically uses local thread-safe JSON persistence with support for Firestore expansion.
"""

import json
import os
import threading
from datetime import datetime, timedelta
import uuid
from departments import (
    CATEGORY_DEPARTMENT_MAP,
    ADMIN_DEPARTMENT_MAP,
    SLA_DAYS_BY_PRIORITY,
    DEFAULT_DAILY_PROCESSING_LIMIT,
    get_department_for_admin,
    get_department_for_category,
)

DB_FILE = os.path.join(os.path.dirname(__file__), "data", "civicroute_db.json")
_lock = threading.Lock()


def _ensure_data_dir():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    if not os.path.exists(DB_FILE):
        initial_data = {
            "users": {},
            "complaints": {},
            "notifications": [],
            "admin_daily_actions": {},  # "email:YYYY-MM-DD": [complaintId, ...]
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=2)


def _load_db() -> dict:
    _ensure_data_dir()
    with _lock:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


def _save_db(data: dict):
    _ensure_data_dir()
    with _lock:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


# ==============================================================================
# USER OPERATIONS
# ==============================================================================

def get_user_by_uid(uid: str) -> dict | None:
    db = _load_db()
    return db["users"].get(uid)


def get_user_by_email(email: str) -> dict | None:
    if not email:
        return None
    db = _load_db()
    norm = email.strip().lower()
    for user in db["users"].values():
        if user.get("email", "").strip().lower() == norm:
            return user
    return None


def upsert_user(user_data: dict) -> dict:
    """Creates or updates a user profile."""
    db = _load_db()
    uid = user_data["uid"]
    existing = db["users"].get(uid, {})
    now = datetime.now().isoformat()
    
    merged = {
        **existing,
        **user_data,
        "updatedAt": now,
    }
    if "createdAt" not in merged:
        merged["createdAt"] = now
    
    # Enforce role logic
    email = merged.get("email", "").strip().lower()
    if email.endswith("@gov.in") and email in ADMIN_DEPARTMENT_MAP:
        merged["role"] = "admin"
        merged["department"] = ADMIN_DEPARTMENT_MAP[email]
    else:
        merged["role"] = "citizen"
        merged.pop("department", None)
        
    db["users"][uid] = merged
    _save_db(db)
    return merged


# ==============================================================================
# SLA & ESCALATION UTILITIES
# ==============================================================================

def calculate_sla_deadline(date_added_iso: str, priority: str) -> str:
    """Calculates SLA deadline based on priority duration."""
    days = SLA_DAYS_BY_PRIORITY.get(priority.upper(), 7)
    try:
        added = datetime.fromisoformat(date_added_iso)
    except Exception:
        added = datetime.now()
    deadline = added + timedelta(days=days)
    return deadline.isoformat()


def update_complaint_sla_status(complaint: dict) -> dict:
    """Dynamically checks if complaint is overdue and flags escalation."""
    status = complaint.get("status", "SUBMITTED")
    if status in ["RESOLVED", "CLOSED"]:
        complaint["slaStatus"] = "COMPLETED"
        return complaint
    
    deadline_str = complaint.get("slaDeadline")
    if not deadline_str:
        return complaint
        
    try:
        deadline = datetime.fromisoformat(deadline_str)
        now = datetime.now()
        if now > deadline:
            complaint["slaStatus"] = "OVERDUE"
            complaint["escalationStatus"] = "ESCALATED"
            if not complaint.get("escalatedDate"):
                complaint["escalatedDate"] = now.isoformat()
            if not complaint.get("escalatedTo"):
                complaint["escalatedTo"] = "Department Senior Officer"
        else:
            diff = deadline - now
            days_left = max(0, diff.days)
            complaint["slaStatus"] = f"{days_left}d remaining"
    except Exception:
        pass
        
    return complaint


# ==============================================================================
# COMPLAINT OPERATIONS
# ==============================================================================

def generate_ticket_id() -> str:
    """Generates unique formatted ticket ID like GOV-10482."""
    db = _load_db()
    existing_ids = set(db["complaints"].keys())
    while True:
        num = str(uuid.uuid4().int)[:5]
        candidate = f"GOV-{num}"
        if candidate not in existing_ids:
            return candidate


def create_complaint(complaint_data: dict) -> dict:
    """Creates a persistent citizen complaint record."""
    db = _load_db()
    ticket_id = complaint_data.get("complaintId") or generate_ticket_id()
    now = datetime.now().isoformat()
    
    priority = complaint_data.get("priority", "MEDIUM").upper()
    if priority not in ["HIGH", "MEDIUM", "LOW"]:
        priority = "MEDIUM"
        
    category = complaint_data.get("category", "Other")
    department = get_department_for_category(category)
    
    record = {
        "complaintId": ticket_id,
        "userId": complaint_data.get("userId", ""),
        "citizenName": complaint_data.get("citizenName", "Citizen"),
        "citizenEmail": complaint_data.get("citizenEmail", ""),
        "title": complaint_data.get("title") or (complaint_data.get("description", "")[:60] + "..."),
        "description": complaint_data.get("description", ""),
        "issues": complaint_data.get("issues", []),
        "category": category,
        "department": department,
        "priority": priority,
        "location": complaint_data.get("location", "Dharmapuri, Tamil Nadu"),
        "latitude": float(complaint_data.get("latitude", 12.1211)),
        "longitude": float(complaint_data.get("longitude", 78.1582)),
        "evidence": complaint_data.get("evidence", []),
        "status": "SUBMITTED",
        "dateAdded": now,
        "createdAt": now,
        "updatedAt": now,
        "slaDeadline": calculate_sla_deadline(now, priority),
        "escalationStatus": "NORMAL",
        "escalatedDate": None,
        "escalatedTo": None,
        "resolutionNote": None,
        "resolutionPhoto": None,
        "resolvedDate": None,
        "resolvedBy": None,
        "resolvingDepartment": None,
    }
    
    record = update_complaint_sla_status(record)
    db["complaints"][ticket_id] = record
    _save_db(db)
    
    # Create submission notification for citizen
    create_notification({
        "userId": record["userId"],
        "title": f"Complaint Submitted: {ticket_id}",
        "message": f"Your complaint '{record['title']}' has been routed to {department}.",
        "type": "submitted",
        "complaintId": ticket_id
    })
    
    return record


def get_complaint_by_id(complaint_id: str) -> dict | None:
    db = _load_db()
    complaint = db["complaints"].get(complaint_id)
    if complaint:
        return update_complaint_sla_status(complaint)
    return None


def get_citizen_complaints(user_id: str) -> list[dict]:
    """Strictly returns only complaints authored by this citizen."""
    db = _load_db()
    results = [
        update_complaint_sla_status(c)
        for c in db["complaints"].values()
        if c.get("userId") == user_id
    ]
    results.sort(key=lambda x: x.get("dateAdded", ""), reverse=True)
    return results


def get_department_complaints(department: str) -> list[dict]:
    """Strictly returns only complaints assigned to this department."""
    db = _load_db()
    dept_norm = department.strip().lower()
    results = [
        update_complaint_sla_status(c)
        for c in db["complaints"].values()
        if c.get("department", "").strip().lower() == dept_norm
    ]
    
    # Priority sorting: 1. Overdue/Escalated, 2. HIGH, 3. MEDIUM, 4. LOW
    def sort_key(c):
        is_overdue = 1 if (c.get("escalationStatus") == "ESCALATED" or "OVERDUE" in c.get("slaStatus", "")) else 0
        p_weight = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(c.get("priority", "MEDIUM"), 0)
        date_str = c.get("dateAdded", "")
        return (is_overdue, p_weight, date_str)
        
    results.sort(key=sort_key, reverse=True)
    return results


def update_complaint_status(complaint_id: str, new_status: str, admin_email: str, department: str) -> tuple[bool, str, dict | None]:
    """Updates complaint status with department authorization check."""
    db = _load_db()
    complaint = db["complaints"].get(complaint_id)
    if not complaint:
        return False, "Complaint not found", None
        
    if complaint.get("department", "").strip().lower() != department.strip().lower():
        return False, "Unauthorized: This complaint belongs to another department", None
        
    now = datetime.now().isoformat()
    complaint["status"] = new_status
    complaint["updatedAt"] = now
    
    # Record admin daily processed action
    record_admin_daily_action(admin_email, complaint_id)
    
    db["complaints"][complaint_id] = update_complaint_sla_status(complaint)
    _save_db(db)
    
    # Citizen notification
    create_notification({
        "userId": complaint["userId"],
        "title": f"Status Update: {complaint_id}",
        "message": f"Your complaint status is now {new_status}.",
        "type": "status_change",
        "complaintId": complaint_id
    })
    
    return True, "Status updated successfully", complaint


def resolve_complaint(complaint_id: str, resolution_note: str, resolution_photo: str | None, admin_email: str, department: str) -> tuple[bool, str, dict | None]:
    """Resolves complaint. Requires mandatory resolution note."""
    if not resolution_note or not resolution_note.strip():
        return False, "Resolution note is required to resolve a complaint.", None
        
    db = _load_db()
    complaint = db["complaints"].get(complaint_id)
    if not complaint:
        return False, "Complaint not found", None
        
    if complaint.get("department", "").strip().lower() != department.strip().lower():
        return False, "Unauthorized: Cannot resolve complaints from another department", None
        
    now = datetime.now().isoformat()
    complaint["status"] = "RESOLVED"
    complaint["resolutionNote"] = resolution_note.strip()
    complaint["resolutionPhoto"] = resolution_photo
    complaint["resolvedDate"] = now
    complaint["resolvedBy"] = admin_email
    complaint["resolvingDepartment"] = department
    complaint["updatedAt"] = now
    complaint["slaStatus"] = "RESOLVED"
    
    # Record admin processing action
    record_admin_daily_action(admin_email, complaint_id)
    
    db["complaints"][complaint_id] = complaint
    _save_db(db)
    
    # In-app citizen notification
    create_notification({
        "userId": complaint["userId"],
        "title": f"Complaint Resolved: {complaint_id}",
        "message": f"Your complaint has been resolved by {department}. Note: {resolution_note[:100]}",
        "type": "resolved",
        "complaintId": complaint_id
    })
    
    return True, "Complaint resolved successfully", complaint


# ==============================================================================
# DAILY PROCESSING LIMIT
# ==============================================================================

def get_admin_daily_processed(admin_email: str) -> dict:
    """Returns processed count, daily limit, and remaining actions today."""
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"{admin_email.strip().lower()}:{today}"
    db = _load_db()
    processed_list = db["admin_daily_actions"].get(key, [])
    processed_count = len(processed_list)
    limit = DEFAULT_DAILY_PROCESSING_LIMIT
    remaining = max(0, limit - processed_count)
    
    return {
        "dailyLimit": limit,
        "processedToday": processed_count,
        "remaining": remaining,
        "limitReached": processed_count >= limit
    }


def record_admin_daily_action(admin_email: str, complaint_id: str):
    """Logs a processed complaint for today's quota."""
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"{admin_email.strip().lower()}:{today}"
    db = _load_db()
    if key not in db["admin_daily_actions"]:
        db["admin_daily_actions"][key] = []
    if complaint_id not in db["admin_daily_actions"][key]:
        db["admin_daily_actions"][key].append(complaint_id)
    _save_db(db)


# ==============================================================================
# NOTIFICATIONS
# ==============================================================================

def create_notification(notif: dict):
    db = _load_db()
    entry = {
        "id": "NOTIF-" + str(uuid.uuid4().int)[:6],
        "userId": notif.get("userId", ""),
        "title": notif.get("title", "Notification"),
        "message": notif.get("message", ""),
        "type": notif.get("type", "info"),
        "complaintId": notif.get("complaintId"),
        "date": datetime.now().isoformat(),
        "read": False
    }
    db["notifications"].append(entry)
    _save_db(db)
    return entry


def get_user_notifications(user_id: str) -> list[dict]:
    db = _load_db()
    results = [n for n in db["notifications"] if n.get("userId") == user_id]
    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    return results
