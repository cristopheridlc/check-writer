# src/ui/register_view.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from ..core.models import Check, Account
from ..core.database import CheckbookDatabase


class RegisterView(Adw.Bin):
    """Checkbook register history and ledger screen."""

    def __init__(self, db: CheckbookDatabase, on_duplicate_check=None, show_toast_cb=None):
        super().__init__()
        self.db = db
        self.on_duplicate_check = on_duplicate_check
        self.show_toast_cb = show_toast_cb
        self._active_status_filter = "All"
        self._search_query = ""

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)

        # 1. Filter & Search Toolbar
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_hexpand(True)
        self.search_entry.set_placeholder_text("Search by payee, memo, or check #...")
        self.search_entry.connect("search-changed", self._on_search_changed)
        toolbar_box.append(self.search_entry)

        # Status Filter DropDown
        status_model = Gtk.StringList.new(["All Statuses", "Issued", "Cleared", "Voided"])
        self.status_dropdown = Gtk.DropDown.new(status_model, None)
        self.status_dropdown.connect("notify::selected", self._on_status_filter_changed)
        toolbar_box.append(self.status_dropdown)

        # Export CSV Button
        export_btn = Gtk.Button(label="Export CSV")
        export_btn.set_icon_name("document-save-symbolic")
        export_btn.connect("clicked", self._on_export_csv_clicked)
        toolbar_box.append(export_btn)

        main_box.append(toolbar_box)

        # 2. Summary Statistics Card
        self.stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.stats_box.set_homogeneous(True)
        self.stats_box.add_css_class("card")
        self.stats_box.set_margin_top(4)
        self.stats_box.set_margin_bottom(8)

        self.total_stat_label = self._create_stat_pill("Total Register", "$0.00")
        self.issued_stat_label = self._create_stat_pill("Issued (Pending)", "$0.00")
        self.cleared_stat_label = self._create_stat_pill("Cleared", "$0.00")
        self.voided_stat_label = self._create_stat_pill("Voided", "$0.00")

        main_box.append(self.stats_box)

        # 3. Scrolled Checks List
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("boxed-list")

        # Empty state page
        self.empty_page = Adw.StatusPage()
        self.empty_page.set_icon_name("emblem-documents-symbolic")
        self.empty_page.set_title("No Checks Found")
        self.empty_page.set_description("Write and save your first check using the Check Writer tab.")
        self.empty_page.set_vexpand(True)

        self.stack = Gtk.Stack()
        self.stack.add_named(self.list_box, "list")
        self.stack.add_named(self.empty_page, "empty")

        self.scrolled.set_child(self.stack)
        main_box.append(self.scrolled)

        self.set_child(main_box)

    def _create_stat_pill(self, title: str, initial_value: str) -> Gtk.Label:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        box.set_margin_end(12)

        t_lbl = Gtk.Label(label=title, xalign=0.5)
        t_lbl.add_css_class("dim-label")
        t_lbl.add_css_class("caption")

        v_lbl = Gtk.Label(label=initial_value, xalign=0.5)
        v_lbl.add_css_class("heading")

        box.append(t_lbl)
        box.append(v_lbl)
        self.stats_box.append(box)
        return v_lbl

    def _on_search_changed(self, entry):
        self._search_query = entry.get_text()
        self.refresh()

    def _on_status_filter_changed(self, dropdown, pspec):
        idx = dropdown.get_selected()
        mapping = {0: "All", 1: "issued", 2: "cleared", 3: "voided"}
        self._active_status_filter = mapping.get(idx, "All")
        self.refresh()

    def refresh(self):
        # Update summary
        summary = self.db.get_register_summary()
        self.total_stat_label.set_text(f"${summary['total_amount']:,.2f}")
        self.issued_stat_label.set_text(f"${summary['issued_amount']:,.2f}")
        self.cleared_stat_label.set_text(f"${summary['cleared_amount']:,.2f}")
        self.voided_stat_label.set_text(f"${summary['voided_amount']:,.2f}")

        # Clear existing rows
        while True:
            row = self.list_box.get_first_child()
            if not row:
                break
            self.list_box.remove(row)

        checks = self.db.get_checks(
            search=self._search_query if self._search_query else None,
            status=self._active_status_filter if self._active_status_filter != "All" else None
        )

        if not checks:
            self.stack.set_visible_child_name("empty")
            return

        self.stack.set_visible_child_name("list")
        for check in checks:
            row = self._create_check_row(check)
            self.list_box.append(row)

    def _create_check_row(self, check: Check) -> Adw.ActionRow:
        row = Adw.ActionRow()
        row.set_title(f"<b>#{check.check_number}</b> — {GLib.markup_escape_text(check.payee or 'Unknown Payee')}")
        row.set_use_markup(True)

        subtitle_parts = [check.date_str]
        if check.memo:
            subtitle_parts.append(f"Memo: {GLib.markup_escape_text(check.memo)}")
        row.set_subtitle(" • ".join(subtitle_parts))

        # Status badge
        status_lbl = Gtk.Label(label=check.status.capitalize())
        status_lbl.set_valign(Gtk.Align.CENTER)
        status_lbl.add_css_class("caption")
        status_lbl.add_css_class("pill")
        if check.status.lower() == "cleared":
            status_lbl.add_css_class("success")
        elif check.status.lower() == "voided":
            status_lbl.add_css_class("error")
        else:
            status_lbl.add_css_class("warning")
        row.add_suffix(status_lbl)

        # Amount label
        amount_lbl = Gtk.Label(label=f"${check.amount:,.2f}")
        amount_lbl.set_valign(Gtk.Align.CENTER)
        amount_lbl.add_css_class("heading")
        if check.status.lower() == "voided":
            amount_lbl.add_css_class("dim-label")
        row.add_suffix(amount_lbl)

        # Actions Menu Button
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("view-more-symbolic")
        menu_btn.set_valign(Gtk.Align.CENTER)
        menu_btn.add_css_class("flat")

        popover_menu = Gio.Menu()

        # Status actions
        if check.status.lower() != "cleared":
            popover_menu.append("Mark as Cleared", f"row.cleared_{check.id}")
        if check.status.lower() != "issued":
            popover_menu.append("Mark as Issued", f"row.issued_{check.id}")
        if check.status.lower() != "voided":
            popover_menu.append("Void Check", f"row.void_{check.id}")

        popover_menu.append("Duplicate in Writer", f"row.duplicate_{check.id}")
        popover_menu.append("Delete", f"row.delete_{check.id}")

        # Connect actions to ActionGroup
        action_group = Gio.SimpleActionGroup()

        def make_status_action(status_val):
            act = Gio.SimpleAction.new(f"{status_val}_{check.id}", None)
            act.connect("activate", lambda *_: self._set_check_status(check.id, status_val))
            action_group.add_action(act)

        make_status_action("cleared")
        make_status_action("issued")
        make_status_action("void")

        dup_act = Gio.SimpleAction.new(f"duplicate_{check.id}", None)
        dup_act.connect("activate", lambda *_: self._duplicate_check(check))
        action_group.add_action(dup_act)

        del_act = Gio.SimpleAction.new(f"delete_{check.id}", None)
        del_act.connect("activate", lambda *_: self._delete_check(check.id))
        action_group.add_action(del_act)

        row.insert_action_group("row", action_group)
        menu_btn.set_menu_model(popover_menu)
        row.add_suffix(menu_btn)

        return row

    def _set_check_status(self, check_id: int, status_val: str):
        real_status = "voided" if status_val == "void" else status_val
        self.db.update_check_status(check_id, real_status)
        self.refresh()
        if self.show_toast_cb:
            self.show_toast_cb(f"Check status updated to {real_status.capitalize()}")

    def _duplicate_check(self, check: Check):
        if self.on_duplicate_check:
            # Create a copy with fresh date and next check number
            dup = Check(
                account_id=check.account_id,
                check_number=check.check_number + 1,
                payee=check.payee,
                amount=check.amount,
                amount_words=check.amount_words,
                memo=check.memo,
                status="issued"
            )
            self.on_duplicate_check(dup)

    def _delete_check(self, check_id: int):
        self.db.delete_check(check_id)
        self.refresh()
        if self.show_toast_cb:
            self.show_toast_cb("Check removed from register")

    def _on_export_csv_clicked(self, button):
        root = self.get_root()
        dialog = Gtk.FileDialog()
        dialog.set_title("Export Checkbook Register to CSV")
        dialog.set_initial_name("checkbook_register.csv")

        def on_save_response(file_dialog, result):
            try:
                gfile = file_dialog.save_finish(result)
                if gfile:
                    file_path = gfile.get_path()
                    count = self.db.export_checks_to_csv(file_path)
                    if self.show_toast_cb:
                        self.show_toast_cb(f"Exported {count} checks to {gfile.get_basename()}")
            except GLib.Error:
                pass  # User canceled

        dialog.save(root, None, on_save_response)
