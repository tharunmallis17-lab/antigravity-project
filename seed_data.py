"""
Demo Seed Data Generator for CivicRoute AI
Populates realistic fictional complaints across all 12 departments,
including normal, high priority, overdue/escalated, and resolved tickets for testing.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime, timedelta
import data_store
from departments import CATEGORY_DEPARTMENT_MAP

DEMO_CITIZEN = {
    "uid": "citizen_demo_user_101",
    "email": "priya.citizen@gmail.com",
    "name": "Priya Sundaram",
    "phone": "+91 98765 43210",
    "language": "Tamil & English",
    "defaultLocation": "Anna Nagar, Dharmapuri, Tamil Nadu",
    "role": "citizen"
}

SEED_COMPLAINTS = [
    # 1. PWD Roads (OVERDUE & ESCALATED)
    {
        "complaintId": "GOV-10482",
        "userId": DEMO_CITIZEN["uid"],
        "citizenName": DEMO_CITIZEN["name"],
        "citizenEmail": DEMO_CITIZEN["email"],
        "title": "Severe potholes near Government Higher Secondary School",
        "description": "Deep potholes on the main road right outside the school gate. Two two-wheelers skidded yesterday. Urgent asphalt patch required.",
        "category": "Roads & Potholes",
        "priority": "HIGH",
        "location": "Near Govt Higher Secondary School, Dharmapuri Main Road",
        "latitude": 12.1265,
        "longitude": 78.1578,
        "status": "IN PROGRESS",
        "days_ago": 5, # Exceeds 3 days HIGH SLA -> OVERDUE
    },
    # 2. PWD Roads (Active HIGH priority)
    {
        "complaintId": "GOV-10512",
        "userId": "citizen_demo_user_102",
        "citizenName": "K. Murugan",
        "citizenEmail": "murugan.k@gmail.com",
        "title": "Road cave-in near Railway Feeder Road",
        "description": "Portion of the road has sunk after recent pipe laying work. Heavy vehicles are getting stuck.",
        "category": "Roads & Potholes",
        "priority": "HIGH",
        "location": "Railway Feeder Road, Dharmapuri",
        "latitude": 12.1280,
        "longitude": 78.1610,
        "status": "SUBMITTED",
        "days_ago": 1,
    },
    # 3. PWD Roads (Resolved with Photo)
    {
        "complaintId": "GOV-10390",
        "userId": DEMO_CITIZEN["uid"],
        "citizenName": DEMO_CITIZEN["name"],
        "citizenEmail": DEMO_CITIZEN["email"],
        "title": "Damaged speed breaker on Bus Stand Road",
        "description": "Broken concrete edges on the speed breaker creating danger for motorists.",
        "category": "Roads & Potholes",
        "priority": "MEDIUM",
        "location": "Bus Stand Approach Road, Dharmapuri",
        "latitude": 12.1215,
        "longitude": 78.1585,
        "status": "RESOLVED",
        "days_ago": 8,
        "resolutionNote": "Damaged section was cleared and re-leveled with bituminous cold mix. Reflective warning paint applied.",
        "resolutionPhoto": "https://images.unsplash.com/photo-1515260268569-9271009adfdb?w=600&auto=format&fit=crop&q=80",
        "resolvedBy": "pwd.admin@gov.in",
        "resolvingDepartment": "Public Works Department (PWD) – Roads Division"
    },
    # 4. Water Board (TWAD) - Emerging Issue cluster
    {
        "complaintId": "GOV-20101",
        "userId": "citizen_demo_user_103",
        "citizenName": "Anitha Rajan",
        "citizenEmail": "anitha.rajan@gmail.com",
        "title": "Drinking water pipeline burst causing road flooding",
        "description": "Main drinking water pipeline ruptured early this morning. Potable water is continuously flowing onto Gandhi Nagar 3rd street.",
        "category": "Water Supply",
        "priority": "HIGH",
        "location": "Gandhi Nagar 3rd Cross, Dharmapuri",
        "latitude": 12.1310,
        "longitude": 78.1540,
        "status": "ASSIGNED",
        "days_ago": 1,
    },
    {
        "complaintId": "GOV-20102",
        "userId": DEMO_CITIZEN["uid"],
        "citizenName": DEMO_CITIZEN["name"],
        "citizenEmail": DEMO_CITIZEN["email"],
        "title": "Low water pressure for consecutive 4 days",
        "description": "Municipal tap supply has had negligible pressure across Anna Nagar Block B.",
        "category": "Water Supply",
        "priority": "MEDIUM",
        "location": "Anna Nagar Block B, Dharmapuri",
        "latitude": 12.1325,
        "longitude": 78.1555,
        "status": "SUBMITTED",
        "days_ago": 2,
    },
    # 5. Street Lighting
    {
        "complaintId": "GOV-30115",
        "userId": DEMO_CITIZEN["uid"],
        "citizenName": DEMO_CITIZEN["name"],
        "citizenEmail": DEMO_CITIZEN["email"],
        "title": "Entire stretch of 6 LED street lights not turning on",
        "description": "Dark stretch on VOC Nagar Main Street poses safety risk for pedestrians after 7 PM.",
        "category": "Street Lighting",
        "priority": "MEDIUM",
        "location": "VOC Nagar Main Street, Dharmapuri",
        "latitude": 12.1190,
        "longitude": 78.1630,
        "status": "IN PROGRESS",
        "days_ago": 4,
    },
    # 6. Waste Management
    {
        "complaintId": "GOV-40120",
        "userId": "citizen_demo_user_104",
        "citizenName": "R. Selvam",
        "citizenEmail": "selvam.r@gmail.com",
        "title": "Overflowing garbage bin near weekly market",
        "description": "Garbage has spilled over 15 feet onto the street; bad odor and stray animals obstructing transit.",
        "category": "Waste Management",
        "priority": "HIGH",
        "location": "Uzhavar Sandhai Market Gate, Dharmapuri",
        "latitude": 12.1240,
        "longitude": 78.1590,
        "status": "SUBMITTED",
        "days_ago": 1,
    },
    # 7. Drainage & Sewage (OVERDUE)
    {
        "complaintId": "GOV-50130",
        "userId": DEMO_CITIZEN["uid"],
        "citizenName": DEMO_CITIZEN["name"],
        "citizenEmail": DEMO_CITIZEN["email"],
        "title": "Open drain overflow during morning hours",
        "description": "Sewerage backflow onto residential footpath creating severe health hazard.",
        "category": "Drainage & Sewage",
        "priority": "HIGH",
        "location": "Kamarajar Colony, Dharmapuri",
        "latitude": 12.1200,
        "longitude": 78.1560,
        "status": "SUBMITTED",
        "days_ago": 4, # Exceeds 3 days HIGH SLA -> OVERDUE
    },
    # 8. Electricity (TANGEDCO)
    {
        "complaintId": "GOV-60145",
        "userId": "citizen_demo_user_105",
        "citizenName": "D. Karthik",
        "citizenEmail": "karthik.d@gmail.com",
        "title": "Sparking transformer near commercial complex",
        "description": "Frequent sparks and buzzing sound from pole-mounted transformer during peak hours.",
        "category": "Electricity",
        "priority": "HIGH",
        "location": "Netaji Road Junction, Dharmapuri",
        "latitude": 12.1275,
        "longitude": 78.1605,
        "status": "IN PROGRESS",
        "days_ago": 1,
    }
]


def seed_database():
    """Initializes demo citizen and complaints."""
    data_store.upsert_user(DEMO_CITIZEN)
    
    for item in SEED_COMPLAINTS:
        days_ago = item.pop("days_ago", 0)
        added_date = datetime.now() - timedelta(days=days_ago)
        item["dateAdded"] = added_date.isoformat()
        item["createdAt"] = added_date.isoformat()
        item["updatedAt"] = added_date.isoformat()
        
        # Priority SLA
        item["slaDeadline"] = data_store.calculate_sla_deadline(item["dateAdded"], item["priority"])
        data_store.create_complaint(item)
        
        # If item has resolution details, apply them
        if item.get("status") == "RESOLVED":
            data_store.resolve_complaint(
                item["complaintId"],
                item.get("resolutionNote", "Issue resolved."),
                item.get("resolutionPhoto"),
                item.get("resolvedBy", "pwd.admin@gov.in"),
                item.get("resolvingDepartment", "Public Works Department (PWD) – Roads Division")
            )

    print("Demo database successfully seeded!")


if __name__ == "__main__":
    seed_database()
