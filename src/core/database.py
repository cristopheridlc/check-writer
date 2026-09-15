# src/core/database.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import csv
import io
import os
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

from .models import Account, Check, Payee, PrintSettings


def get_default_db_path() -> str:
    """Get the standard XDG data directory path for the database."""
    xdg_data = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    app_data_dir = os.path.join(xdg_data, "check-writer")
    os.makedirs(app_data_dir, exist_ok=True)
    return os.path.join(app_data_dir, "checkwriter.db")


class CheckbookDatabase:
    """SQLite database manager for CheckWriter."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_default_db_path()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Create tables if they don't exist and seed default account if needed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    routing_number TEXT NOT NULL,
                    account_number TEXT NOT NULL,
                    next_check_number INTEGER NOT NULL DEFAULT 1001,
                    payor_name TEXT NOT NULL,
                    payor_address1 TEXT,
                    payor_address2 TEXT,
                    payor_phone TEXT,
                    is_default INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # Payees table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    default_memo TEXT,
                    category TEXT DEFAULT 'General',
                    address TEXT,
                    phone TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Checks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    check_number INTEGER NOT NULL,
                    date_str TEXT NOT NULL,
                    payee TEXT NOT NULL,
                    amount REAL NOT NULL,
                    amount_words TEXT NOT NULL,
                    memo TEXT,
                    status TEXT NOT NULL DEFAULT 'issued',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE SET NULL
                )
            """)

            # Settings key-value table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Check if any account exists; if not, create a default account
            cursor.execute("SELECT COUNT(*) FROM accounts")
            if cursor.fetchone()[0] == 0:
                default_account = Account(
                    name="Primary Checking",
                    bank_name="First National Bank",
                    routing_number="123456789",
                    account_number="9876543210",
                    next_check_number=1001,
                    payor_name="Jane Doe",
                    payor_address1="123 Main Street",
                    payor_address2="Anytown, CA 90210",
                    payor_phone="(555) 000-1234",
                    is_default=True,
                )
                self._insert_account(cursor, default_account)

            conn.commit()

    # --- Account Methods ---

    def _insert_account(self, cursor: sqlite3.Cursor, acc: Account) -> int:
        cursor.execute("""
            INSERT INTO accounts (
                name, bank_name, routing_number, account_number,
                next_check_number, payor_name, payor_address1,
                payor_address2, payor_phone, is_default, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            acc.name, acc.bank_name, acc.routing_number, acc.account_number,
            acc.next_check_number, acc.payor_name, acc.payor_address1,
            acc.payor_address2, acc.payor_phone, 1 if acc.is_default else 0,
            acc.created_at
        ))
        return cursor.lastrowid

    def get_accounts(self) -> List[Account]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts ORDER BY is_default DESC, name ASC")
            rows = cursor.fetchall()
            return [self._row_to_account(r) for r in rows]

    def get_default_account(self) -> Account:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE is_default = 1 LIMIT 1")
            row = cursor.fetchone()
            if row:
                return self._row_to_account(row)
            # Fallback to first account
            cursor.execute("SELECT * FROM accounts LIMIT 1")
            row = cursor.fetchone()
            if row:
                return self._row_to_account(row)
            # Create if none
            acc = Account()
            acc.id = self._insert_account(cursor, acc)
            conn.commit()
            return acc

    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            return self._row_to_account(row) if row else None

    def save_account(self, acc: Account) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if acc.is_default:
                cursor.execute("UPDATE accounts SET is_default = 0")

            if acc.id is None:
                acc.id = self._insert_account(cursor, acc)
            else:
                cursor.execute("""
                    UPDATE accounts SET
                        name = ?, bank_name = ?, routing_number = ?, account_number = ?,
                        next_check_number = ?, payor_name = ?, payor_address1 = ?,
                        payor_address2 = ?, payor_phone = ?, is_default = ?
                    WHERE id = ?
                """, (
                    acc.name, acc.bank_name, acc.routing_number, acc.account_number,
                    acc.next_check_number, acc.payor_name, acc.payor_address1,
                    acc.payor_address2, acc.payor_phone, 1 if acc.is_default else 0,
                    acc.id
                ))
            conn.commit()
            return acc.id

    def delete_account(self, account_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM accounts")
            if cursor.fetchone()[0] <= 1:
                return False  # Cannot delete the only account
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            # Ensure at least one default
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE is_default = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute("UPDATE accounts SET is_default = 1 WHERE id = (SELECT id FROM accounts LIMIT 1)")
            conn.commit()
            return True

    def increment_next_check_number(self, account_id: int) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT next_check_number FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            if not row:
                return 1001
            current = row[0]
            new_num = current + 1
            cursor.execute("UPDATE accounts SET next_check_number = ? WHERE id = ?", (new_num, account_id))
            conn.commit()
            return new_num

    # --- Payee Methods ---

    def get_payees(self, search: Optional[str] = None) -> List[Payee]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if search:
                term = f"%{search.strip()}%"
                cursor.execute("""
                    SELECT * FROM payees
                    WHERE name LIKE ? OR default_memo LIKE ? OR category LIKE ?
                    ORDER BY name ASC
                """, (term, term, term))
            else:
                cursor.execute("SELECT * FROM payees ORDER BY name ASC")
            return [self._row_to_payee(r) for r in cursor.fetchall()]

    def get_payee_by_name(self, name: str) -> Optional[Payee]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payees WHERE LOWER(name) = LOWER(?)", (name.strip(),))
            row = cursor.fetchone()
            return self._row_to_payee(row) if row else None

    def save_payee(self, payee: Payee) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if payee.id is None:
                cursor.execute("""
                    INSERT OR REPLACE INTO payees (name, default_memo, category, address, phone, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    payee.name.strip(), payee.default_memo, payee.category,
                    payee.address, payee.phone, payee.notes, payee.created_at
                ))
                payee.id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE payees SET
                        name = ?, default_memo = ?, category = ?,
                        address = ?, phone = ?, notes = ?
                    WHERE id = ?
                """, (
                    payee.name.strip(), payee.default_memo, payee.category,
                    payee.address, payee.phone, payee.notes, payee.id
                ))
            conn.commit()
            return payee.id

    def delete_payee(self, payee_id: int) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM payees WHERE id = ?", (payee_id,))
            conn.commit()

    # --- Check Register Methods ---

    def save_check(self, check: Check, auto_save_payee: bool = True) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now().isoformat()
            check.updated_at = now_iso

            if check.id is None:
                cursor.execute("""
                    INSERT INTO checks (
                        account_id, check_number, date_str, payee, amount,
                        amount_words, memo, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    check.account_id, check.check_number, check.date_str,
                    check.payee.strip(), check.amount, check.amount_words,
                    check.memo, check.status, check.created_at, check.updated_at
                ))
                check.id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE checks SET
                        account_id = ?, check_number = ?, date_str = ?, payee = ?,
                        amount = ?, amount_words = ?, memo = ?, status = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    check.account_id, check.check_number, check.date_str,
                    check.payee.strip(), check.amount, check.amount_words,
                    check.memo, check.status, check.updated_at, check.id
                ))

            # Auto-save payee if not already existing
            if auto_save_payee and check.payee.strip():
                cursor.execute("SELECT id FROM payees WHERE LOWER(name) = LOWER(?)", (check.payee.strip(),))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO payees (name, default_memo, category, created_at)
                        VALUES (?, ?, 'General', ?)
                    """, (check.payee.strip(), check.memo, now_iso))

            conn.commit()
            return check.id

    def get_checks(
        self,
        account_id: Optional[int] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 200,
        offset: int = 0
    ) -> List[Check]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM checks WHERE 1=1"
            params: List[Any] = []

            if account_id is not None:
                query += " AND account_id = ?"
                params.append(account_id)

            if status and status.lower() != "all":
                query += " AND LOWER(status) = LOWER(?)"
                params.append(status)

            if search:
                term = f"%{search.strip()}%"
                query += " AND (payee LIKE ? OR memo LIKE ? OR CAST(check_number AS TEXT) LIKE ?)"
                params.extend([term, term, term])

            query += " ORDER BY date_str DESC, check_number DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, tuple(params))
            return [self._row_to_check(r) for r in cursor.fetchall()]

    def get_check_by_id(self, check_id: int) -> Optional[Check]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM checks WHERE id = ?", (check_id,))
            row = cursor.fetchone()
            return self._row_to_check(row) if row else None

    def update_check_status(self, check_id: int, status: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE checks SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.now().isoformat(), check_id)
            )
            conn.commit()

    def delete_check(self, check_id: int) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checks WHERE id = ?", (check_id,))
            conn.commit()

    def get_register_summary(self, account_id: Optional[int] = None) -> Dict[str, Any]:
        """Get summary statistics for the checkbook register."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT status, COUNT(*), SUM(amount) FROM checks WHERE 1=1"
            params: List[Any] = []
            if account_id is not None:
                query += " AND account_id = ?"
                params.append(account_id)
            query += " GROUP BY status"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            summary = {
                "total_count": 0,
                "total_amount": 0.0,
                "issued_count": 0,
                "issued_amount": 0.0,
                "cleared_count": 0,
                "cleared_amount": 0.0,
                "voided_count": 0,
                "voided_amount": 0.0,
            }

            for row in rows:
                stat = (row[0] or "").lower()
                cnt = row[1] or 0
                amt = row[2] or 0.0

                summary["total_count"] += cnt
                if stat != "voided":
                    summary["total_amount"] += amt

                if stat == "issued":
                    summary["issued_count"] = cnt
                    summary["issued_amount"] = amt
                elif stat == "cleared":
                    summary["cleared_count"] = cnt
                    summary["cleared_amount"] = amt
                elif stat == "voided":
                    summary["voided_count"] = cnt
                    summary["voided_amount"] = amt

            return summary

    def export_checks_to_csv(self, file_path: str, account_id: Optional[int] = None) -> int:
        """Export checks register to a CSV file. Returns number of rows exported."""
        checks = self.get_checks(account_id=account_id, limit=100000)
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Check #", "Date", "Payee", "Amount ($)", "Amount in Words", "Memo", "Status"])
            for c in checks:
                writer.writerow([
                    c.check_number,
                    c.date_str,
                    c.payee,
                    f"{c.amount:.2f}",
                    c.amount_words,
                    c.memo,
                    c.status.capitalize()
                ])
        return len(checks)

    # --- Setting key-values ---

    def get_setting(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    # --- Helper Row Mappers ---

    @staticmethod
    def _row_to_account(r: sqlite3.Row) -> Account:
        return Account(
            id=r["id"],
            name=r["name"],
            bank_name=r["bank_name"],
            routing_number=r["routing_number"],
            account_number=r["account_number"],
            next_check_number=r["next_check_number"],
            payor_name=r["payor_name"],
            payor_address1=r["payor_address1"] or "",
            payor_address2=r["payor_address2"] or "",
            payor_phone=r["payor_phone"] or "",
            is_default=bool(r["is_default"]),
            created_at=r["created_at"]
        )

    @staticmethod
    def _row_to_payee(r: sqlite3.Row) -> Payee:
        return Payee(
            id=r["id"],
            name=r["name"],
            default_memo=r["default_memo"] or "",
            category=r["category"] or "General",
            address=r["address"] or "",
            phone=r["phone"] or "",
            notes=r["notes"] or "",
            created_at=r["created_at"]
        )

    @staticmethod
    def _row_to_check(r: sqlite3.Row) -> Check:
        return Check(
            id=r["id"],
            account_id=r["account_id"],
            check_number=r["check_number"],
            date_str=r["date_str"],
            payee=r["payee"],
            amount=float(r["amount"]),
            amount_words=r["amount_words"],
            memo=r["memo"] or "",
            status=r["status"],
            created_at=r["created_at"],
            updated_at=r["updated_at"]
        )
