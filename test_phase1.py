"""
Automated Test Suite for Phase 1: Authentication & Roles
Tests:
1. Citizen Google Login & Profile Creation
2. Citizen attempting to access protected admin endpoint -> 403 Forbidden
3. Approved Admin Login (pwd.admin@gov.in) -> 200 OK + correct PWD Department
4. Unknown @gov.in account (unknown.admin@gov.in) -> 403 Forbidden
5. Department mapping verification for multiple admin accounts (water, electricity, police)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from app import app
import departments
import data_store


class Phase1AuthTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_1_citizen_google_login(self):
        """Verify citizen can sign in with Google payload and obtain valid token."""
        payload = {
            "email": "priya.citizen@gmail.com",
            "name": "Priya Sundaram",
            "phone": "+91 98765 43210"
        }
        res = self.client.post("/api/auth/google", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "citizen")
        self.assertEqual(data["user"]["email"], "priya.citizen@gmail.com")

    def test_2_citizen_cannot_access_admin_route(self):
        """Verify citizen token receives 403 Forbidden when attempting to access /api/admin/verify."""
        # 1. Login as citizen
        res_login = self.client.post("/api/auth/google", json={
            "email": "priya.citizen@gmail.com",
            "name": "Priya Sundaram"
        })
        citizen_token = res_login.get_json()["token"]

        # 2. Attempt admin access
        res = self.client.get("/api/admin/verify", headers={
            "Authorization": f"Bearer {citizen_token}"
        })
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertIn("error", data)
        print("Test 2 Passed: Citizen access to admin route was strictly rejected with 403 Forbidden.")

    def test_3_approved_admin_login_and_access(self):
        """Verify pwd.admin@gov.in logs in successfully and accesses PWD admin scope."""
        res_login = self.client.post("/api/auth/admin-login", json={
            "email": "pwd.admin@gov.in",
            "password": departments.DEFAULT_ADMIN_PASSWORD
        })
        self.assertEqual(res_login.status_code, 200)
        data = res_login.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["department"], "Public Works Department (PWD) – Roads Division")
        admin_token = data["token"]

        # Access protected admin endpoint
        res = self.client.get("/api/admin/verify", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        self.assertEqual(res.status_code, 200)
        verify_data = res.get_json()
        self.assertTrue(verify_data["authorized"])
        self.assertEqual(verify_data["department"], "Public Works Department (PWD) – Roads Division")
        print("Test 3 Passed: Approved admin logged in and verified with correct PWD department.")

    def test_4_unknown_gov_account_rejected(self):
        """Verify unknown @gov.in account is strictly rejected with 403."""
        res = self.client.post("/api/auth/admin-login", json={
            "email": "unknown.admin@gov.in",
            "password": departments.DEFAULT_ADMIN_PASSWORD
        })
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertIn("Access Denied", data["error"])
        print("Test 4 Passed: Unknown @gov.in account was rejected with 403.")

    def test_5_multiple_department_mappings(self):
        """Verify other approved accounts map strictly to their respective departments."""
        test_accounts = [
            ("water.admin@gov.in", "Tamil Nadu Water Supply and Drainage Board (TWAD Board)"),
            ("electricity.admin@gov.in", "Tamil Nadu Generation and Distribution Corporation (TANGEDCO)"),
            ("police.admin@gov.in", "Tamil Nadu Police – Local Police Station"),
            ("municipal.waste.admin@gov.in", "Municipal Corporation – Solid Waste Management Department")
        ]

        for email, expected_dept in test_accounts:
            res = self.client.post("/api/auth/admin-login", json={
                "email": email,
                "password": departments.DEFAULT_ADMIN_PASSWORD
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["department"], expected_dept)

        print("Test 5 Passed: All tested @gov.in accounts mapped to their exact departments.")


if __name__ == "__main__":
    unittest.main()
