"""
Central Configuration for CivicRoute AI
Intelligent Citizen Complaint Routing & Department Grievance Management System

Defines:
1. Controlled Category -> Department mapping
2. Approved Admin Email -> Department mapping
3. Demo Admin credentials & authorization
4. SLA standards & daily quotas
"""

# ==============================================================================
# CONTROLLED CATEGORY -> DEPARTMENT MAPPING (TAMIL NADU CIVIC JURISDICTIONS)
# ==============================================================================

CATEGORY_DEPARTMENT_MAP = {
    "Roads & Potholes": "Public Works Department (PWD) – Roads Division",
    "Water Supply": "Tamil Nadu Water Supply and Drainage Board (TWAD Board)",
    "Electricity": "Tamil Nadu Generation and Distribution Corporation (TANGEDCO)",
    "Waste Management": "Municipal Corporation – Solid Waste Management Department",
    "Drainage & Sewage": "Municipal Corporation – Sewerage & Drainage Department",
    "Public Transport": "Metropolitan Transport Corporation (MTC) / State Transport Corporation",
    "Street Lighting": "Municipal Corporation – Electrical / Street Lighting Division",
    "Public Safety": "Tamil Nadu Police – Local Police Station",
    "Parks & Public Spaces": "Municipal Corporation – Parks & Open Spaces Department",
    "Government Services": "District Collectorate / District Administration",
    "Noise Pollution": "Tamil Nadu Pollution Control Board (TNPCB) – District Office",
    "Other": "Municipal Corporation – Public Grievance Cell",
}

# Reverse index: Department -> Primary Category
DEPARTMENT_TO_PRIMARY_CATEGORY = {
    dept: cat for cat, dept in CATEGORY_DEPARTMENT_MAP.items()
}

# ==============================================================================
# APPROVED ADMIN EMAIL -> DEPARTMENT MAPPING (PROTOTYPE DEMO ACCOUNTS)
# ==============================================================================

ADMIN_DEPARTMENT_MAP = {
    "pwd.admin@gov.in": "Public Works Department (PWD) – Roads Division",
    "water.admin@gov.in": "Tamil Nadu Water Supply and Drainage Board (TWAD Board)",
    "electricity.admin@gov.in": "Tamil Nadu Generation and Distribution Corporation (TANGEDCO)",
    "municipal.waste.admin@gov.in": "Municipal Corporation – Solid Waste Management Department",
    "municipal.drainage.admin@gov.in": "Municipal Corporation – Sewerage & Drainage Department",
    "transport.admin@gov.in": "Metropolitan Transport Corporation (MTC) / State Transport Corporation",
    "streetlight.admin@gov.in": "Municipal Corporation – Electrical / Street Lighting Division",
    "police.admin@gov.in": "Tamil Nadu Police – Local Police Station",
    "parks.admin@gov.in": "Municipal Corporation – Parks & Open Spaces Department",
    "collectorate.admin@gov.in": "District Collectorate / District Administration",
    "tnpcb.admin@gov.in": "Tamil Nadu Pollution Control Board (TNPCB) – District Office",
    "grievance.admin@gov.in": "Municipal Corporation – Public Grievance Cell",
}

# Default demo password for all pre-configured demo admin accounts
DEFAULT_ADMIN_PASSWORD = "Admin@gov2026"

# ==============================================================================
# SLA STANDARDS (IN DAYS)
# ==============================================================================

SLA_DAYS_BY_PRIORITY = {
    "HIGH": 3,
    "MEDIUM": 7,
    "LOW": 15,
}

# Default daily processing limit per admin
DEFAULT_DAILY_PROCESSING_LIMIT = 5

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_department_for_category(category: str) -> str:
    """Returns normalized department name for category, default to Public Grievance Cell."""
    if not category:
        return CATEGORY_DEPARTMENT_MAP["Other"]
    for valid_cat, dept in CATEGORY_DEPARTMENT_MAP.items():
        if valid_cat.lower() == category.strip().lower():
            return dept
    return CATEGORY_DEPARTMENT_MAP["Other"]


def get_department_for_admin(email: str) -> str | None:
    """Returns assigned department if email is an approved @gov.in admin, else None."""
    if not email:
        return None
    normalized_email = email.strip().lower()
    return ADMIN_DEPARTMENT_MAP.get(normalized_email)


def is_valid_admin_email(email: str) -> bool:
    """Validates whether email is an approved government admin account."""
    if not email:
        return False
    normalized = email.strip().lower()
    return normalized.endswith("@gov.in") and normalized in ADMIN_DEPARTMENT_MAP


def get_all_approved_admins() -> list[dict]:
    """Returns list of approved demo accounts for documentation / demo switcher."""
    return [
        {
            "email": email,
            "department": dept,
            "defaultPassword": DEFAULT_ADMIN_PASSWORD
        }
        for email, dept in ADMIN_DEPARTMENT_MAP.items()
    ]
