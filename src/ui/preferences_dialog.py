# src/ui/preferences_dialog.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from ..core.models import Account, PrintSettings
from ..core.database import CheckbookDatabase


class PreferencesDialog(Adw.PreferencesWindow):
    """Preferences window for CheckWriter."""

    def __init__(self, parent_window: Gtk.Window, db: CheckbookDatabase, on_saved=None):
        super().__init__(transient_for=parent_window, modal=True)
        self.db = db
        self.on_saved = on_saved
        self.set_title("Preferences")
        self.set_default_size(640, 520)

        self._build_accounts_page()
        self._build_printing_page()
        self._build_formatting_page()

    def _build_accounts_page(self):
        page = Adw.PreferencesPage()
        page.set_title("Accounts")
        page.set_icon_name("bank-card-symbolic")

        group = Adw.PreferencesGroup()
        group.set_title("Bank Account & Payor Profile")
        group.set_description("Information printed on your check headers and MICR line.")

        account = self.db.get_default_account()
        self._current_account = account

        self.acc_name_row = Adw.EntryRow(title="Account Label")
        self.acc_name_row.set_text(account.name)
        group.add(self.acc_name_row)

        self.bank_name_row = Adw.EntryRow(title="Bank Name")
        self.bank_name_row.set_text(account.bank_name)
        group.add(self.bank_name_row)

        self.routing_row = Adw.EntryRow(title="Routing Number (9 digits)")
        self.routing_row.set_text(account.routing_number)
        group.add(self.routing_row)

        self.acc_num_row = Adw.EntryRow(title="Account Number")
        self.acc_num_row.set_text(account.account_number)
        group.add(self.acc_num_row)

        self.next_chk_row = Adw.EntryRow(title="Next Check Number")
        self.next_chk_row.set_text(str(account.next_check_number))
        group.add(self.next_chk_row)

        # Payor details
        payor_group = Adw.PreferencesGroup()
        payor_group.set_title("Payor Details (Your Info)")

        self.payor_name_row = Adw.EntryRow(title="Your Full Name / Business")
        self.payor_name_row.set_text(account.payor_name)
        payor_group.add(self.payor_name_row)

        self.payor_addr1_row = Adw.EntryRow(title="Address Line 1")
        self.payor_addr1_row.set_text(account.payor_address1)
        payor_group.add(self.payor_addr1_row)

        self.payor_addr2_row = Adw.EntryRow(title="Address Line 2 (City, State ZIP)")
        self.payor_addr2_row.set_text(account.payor_address2)
        payor_group.add(self.payor_addr2_row)

        self.payor_phone_row = Adw.EntryRow(title="Phone Number")
        self.payor_phone_row.set_text(account.payor_phone)
        payor_group.add(self.payor_phone_row)

        page.add(group)
        page.add(payor_group)
        self.add(page)

    def _build_printing_page(self):
        page = Adw.PreferencesPage()
        page.set_title("Printing")
        page.set_icon_name("printer-symbolic")

        # Layout group
        layout_group = Adw.PreferencesGroup()
        layout_group.set_title("Check Layout & Paper Type")

        self.layout_row = Adw.ComboRow(title="Default Format")
        layout_model = Gtk.StringList.new([
            "Personal / Wallet Single Check (6.0\" x 2.75\")",
            "Business Voucher Check (Top Check + 2 Stubs)",
            "3-Per-Page Sheet"
        ])
        self.layout_row.set_model(layout_model)

        current_layout = self.db.get_setting("layout", "personal_single")
        layout_idx = {"personal_single": 0, "voucher_top": 1, "three_per_page": 2}.get(current_layout, 0)
        self.layout_row.set_selected(layout_idx)
        layout_group.add(self.layout_row)

        # Calibration group
        cal_group = Adw.PreferencesGroup()
        cal_group.set_title("Printer Calibration & Margins")
        cal_group.set_description("Fine-tune check print alignment on pre-printed check stock.")

        self.offset_x_row = Adw.SpinRow.new_with_range(-50.0, 50.0, 0.5)
        self.offset_x_row.set_title("Horizontal Offset X (mm)")
        self.offset_x_row.set_value(float(self.db.get_setting("offset_x_mm", "0.0") or 0.0))
        cal_group.add(self.offset_x_row)

        self.offset_y_row = Adw.SpinRow.new_with_range(-50.0, 50.0, 0.5)
        self.offset_y_row.set_title("Vertical Offset Y (mm)")
        self.offset_y_row.set_value(float(self.db.get_setting("offset_y_mm", "0.0") or 0.0))
        cal_group.add(self.offset_y_row)

        page.add(layout_group)
        page.add(cal_group)
        self.add(page)

    def _build_formatting_page(self):
        page = Adw.PreferencesPage()
        page.set_title("Formatting")
        page.set_icon_name("format-text-bold-symbolic")

        sec_group = Adw.PreferencesGroup()
        sec_group.set_title("Security & Styling")

        self.sec_stars_row = Adw.SwitchRow(title="Security Fill Asterisks (***)")
        self.sec_stars_row.set_subtitle("Wrap amounts with asterisks to prevent fraudulent alteration")
        self.sec_stars_row.set_active(self.db.get_setting("security_fill", "true").lower() == "true")
        sec_group.add(self.sec_stars_row)

        self.casing_row = Adw.ComboRow(title="Legal Words Casing")
        casing_model = Gtk.StringList.new(["Title Case", "UPPERCASE", "lowercase"])
        self.casing_row.set_model(casing_model)
        cur_casing = self.db.get_setting("casing", "Title").lower()
        casing_idx = {"title": 0, "uppercase": 1, "lowercase": 2}.get(cur_casing, 0)
        self.casing_row.set_selected(casing_idx)
        sec_group.add(self.casing_row)

        page.add(sec_group)
        self.add(page)

        # Save changes when window closes
        self.connect("close-request", self._on_close_save)

    def _on_close_save(self, window):
        # Save account
        acc = self._current_account
        acc.name = self.acc_name_row.get_text().strip() or "Primary Checking"
        acc.bank_name = self.bank_name_row.get_text().strip()
        acc.routing_number = self.routing_row.get_text().strip()
        acc.account_number = self.acc_num_row.get_text().strip()
        chk_str = self.next_chk_row.get_text().strip()
        acc.next_check_number = int(chk_str) if chk_str.isdigit() else 1001
        acc.payor_name = self.payor_name_row.get_text().strip()
        acc.payor_address1 = self.payor_addr1_row.get_text().strip()
        acc.payor_address2 = self.payor_addr2_row.get_text().strip()
        acc.payor_phone = self.payor_phone_row.get_text().strip()
        self.db.save_account(acc)

        # Save layout settings
        layout_map = {0: "personal_single", 1: "voucher_top", 2: "three_per_page"}
        self.db.set_setting("layout", layout_map.get(self.layout_row.get_selected(), "personal_single"))
        self.db.set_setting("offset_x_mm", str(self.offset_x_row.get_value()))
        self.db.set_setting("offset_y_mm", str(self.offset_y_row.get_value()))
        self.db.set_setting("security_fill", "true" if self.sec_stars_row.get_active() else "false")

        casing_map = {0: "Title", 1: "UPPERCASE", 2: "lowercase"}
        self.db.set_setting("casing", casing_map.get(self.casing_row.get_selected(), "Title"))

        if self.on_saved:
            self.on_saved()

        return False
