# src/core/models.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Account:
    id: Optional[int] = None
    name: str = "Primary Checking"
    bank_name: str = "My Bank"
    routing_number: str = "123456789"
    account_number: str = "9876543210"
    next_check_number: int = 1001
    payor_name: str = "Jane Doe"
    payor_address1: str = "123 Main Street"
    payor_address2: str = "Anytown, CA 90210"
    payor_phone: str = "(555) 000-1234"
    is_default: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Payee:
    id: Optional[int] = None
    name: str = ""
    default_memo: str = ""
    category: str = "General"
    address: str = ""
    phone: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Check:
    id: Optional[int] = None
    account_id: Optional[int] = None
    check_number: int = 1001
    date_str: str = field(default_factory=lambda: date.today().strftime("%Y-%m-%d"))
    payee: str = ""
    amount: float = 0.0
    amount_words: str = ""
    memo: str = ""
    status: str = "issued"  # 'issued', 'cleared', 'voided'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PrintSettings:
    layout: str = "personal_single"  # 'personal_single', 'voucher_top', 'three_per_page'
    page_position: int = 0  # 0=Top, 1=Middle, 2=Bottom (for three_per_page)
    offset_x_mm: float = 0.0
    offset_y_mm: float = 0.0
    print_micr: bool = True
    print_payor_info: bool = True
    print_bank_info: bool = True
    security_fill: bool = True
    casing: str = "Title"  # 'Title', 'UPPERCASE', 'lowercase'
