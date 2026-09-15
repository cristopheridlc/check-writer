# tests/test_database.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import tempfile
import unittest
from src.core.models import Account, Check, Payee
from src.core.database import CheckbookDatabase


class TestCheckbookDatabase(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_checkwriter.db")
        self.db = CheckbookDatabase(self.db_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_default_account_created(self):
        accounts = self.db.get_accounts()
        self.assertGreaterEqual(len(accounts), 1)
        default_acc = self.db.get_default_account()
        self.assertIsNotNone(default_acc)
        self.assertTrue(default_acc.is_default)

    def test_save_and_retrieve_check(self):
        acc = self.db.get_default_account()
        check = Check(
            account_id=acc.id,
            check_number=1001,
            date_str="2026-09-15",
            payee="Acme Corp",
            amount=500.25,
            amount_words="Five Hundred and 25/100 Dollars",
            memo="Monthly Rent",
            status="issued"
        )
        check_id = self.db.save_check(check)
        self.assertIsNotNone(check_id)

        retrieved = self.db.get_check_by_id(check_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.payee, "Acme Corp")
        self.assertEqual(retrieved.amount, 500.25)
        self.assertEqual(retrieved.status, "issued")

        # Check payee auto-created
        payee = self.db.get_payee_by_name("Acme Corp")
        self.assertIsNotNone(payee)
        self.assertEqual(payee.name, "Acme Corp")

    def test_update_check_status(self):
        acc = self.db.get_default_account()
        check = Check(
            account_id=acc.id,
            check_number=1002,
            payee="Utility Co",
            amount=75.0,
            amount_words="Seventy-Five and 00/100 Dollars",
            status="issued"
        )
        check_id = self.db.save_check(check)
        self.db.update_check_status(check_id, "cleared")

        retrieved = self.db.get_check_by_id(check_id)
        self.assertEqual(retrieved.status, "cleared")

    def test_search_and_filter_checks(self):
        acc = self.db.get_default_account()
        self.db.save_check(Check(account_id=acc.id, check_number=101, payee="Grocery Store", amount=80.0, status="issued"))
        self.db.save_check(Check(account_id=acc.id, check_number=102, payee="Electric Power", amount=120.0, status="cleared"))
        self.db.save_check(Check(account_id=acc.id, check_number=103, payee="Water Utility", amount=45.0, status="voided"))

        # Search by name
        results = self.db.get_checks(search="Electric")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].payee, "Electric Power")

        # Filter by status
        cleared = self.db.get_checks(status="cleared")
        self.assertEqual(len(cleared), 1)
        self.assertEqual(cleared[0].payee, "Electric Power")

        voided = self.db.get_checks(status="voided")
        self.assertEqual(len(voided), 1)
        self.assertEqual(voided[0].payee, "Water Utility")

    def test_register_summary(self):
        acc = self.db.get_default_account()
        self.db.save_check(Check(account_id=acc.id, check_number=1, payee="A", amount=100.0, status="issued"))
        self.db.save_check(Check(account_id=acc.id, check_number=2, payee="B", amount=200.0, status="cleared"))
        self.db.save_check(Check(account_id=acc.id, check_number=3, payee="C", amount=50.0, status="voided"))

        summary = self.db.get_register_summary()
        self.assertEqual(summary["total_count"], 3)
        self.assertEqual(summary["total_amount"], 300.0)  # voided not included in valid balance
        self.assertEqual(summary["issued_amount"], 100.0)
        self.assertEqual(summary["cleared_amount"], 200.0)
        self.assertEqual(summary["voided_amount"], 50.0)

    def test_export_csv(self):
        acc = self.db.get_default_account()
        self.db.save_check(Check(account_id=acc.id, check_number=1, payee="Vendor A", amount=150.0, status="issued"))
        csv_path = os.path.join(self.tmp_dir.name, "export.csv")
        count = self.db.export_checks_to_csv(csv_path)
        self.assertGreaterEqual(count, 1)
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Vendor A", content)
            self.assertIn("150.00", content)


if __name__ == "__main__":
    unittest.main()
