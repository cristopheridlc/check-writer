# src/ui/payees_view.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

from ..core.models import Payee
from ..core.database import CheckbookDatabase


class PayeeEditDialog(Adw.MessageDialog):
    """Dialog to create or edit a Payee."""

    def __init__(self, parent_window: Gtk.Window, payee: Payee = None, on_saved=None):
        super().__init__(
            transient_for=parent_window,
            heading="Edit Payee" if (payee and payee.id) else "New Payee",
            body="Save payee details for automatic completion and default memo."
        )
        self.payee = payee or Payee()
        self.on_saved = on_saved

        self.add_response("cancel", "Cancel")
        self.add_response("save", "Save")
        self.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        # Form content
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        pref_group = Adw.PreferencesGroup()

        self.name_row = Adw.EntryRow(title="Payee Name")
        self.name_row.set_text(self.payee.name)
        pref_group.add(self.name_row)

        self.memo_row = Adw.EntryRow(title="Default Memo")
        self.memo_row.set_text(self.payee.default_memo)
        pref_group.add(self.memo_row)

        self.category_row = Adw.EntryRow(title="Category")
        self.category_row.set_text(self.payee.category)
        pref_group.add(self.category_row)

        self.address_row = Adw.EntryRow(title="Address")
        self.address_row.set_text(self.payee.address)
        pref_group.add(self.address_row)

        box.append(pref_group)
        self.set_extra_child(box)
        self.connect("response", self._on_response)

    def _on_response(self, dialog, response):
        if response == "save":
            name = self.name_row.get_text().strip()
            if not name:
                return
            self.payee.name = name
            self.payee.default_memo = self.memo_row.get_text().strip()
            self.payee.category = self.category_row.get_text().strip() or "General"
            self.payee.address = self.address_row.get_text().strip()
            if self.on_saved:
                self.on_saved(self.payee)


class PayeesView(Adw.Bin):
    """Payees management screen."""

    def __init__(self, db: CheckbookDatabase, show_toast_cb=None):
        super().__init__()
        self.db = db
        self.show_toast_cb = show_toast_cb
        self._search_query = ""

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)

        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_hexpand(True)
        self.search_entry.set_placeholder_text("Search payees...")
        self.search_entry.connect("search-changed", self._on_search_changed)
        toolbar.append(self.search_entry)

        add_btn = Gtk.Button(label="New Payee")
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_payee_clicked)
        toolbar.append(add_btn)

        main_box.append(toolbar)

        # Scrolled List
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("boxed-list")

        self.empty_page = Adw.StatusPage()
        self.empty_page.set_icon_name("system-users-symbolic")
        self.empty_page.set_title("No Payees Saved")
        self.empty_page.set_description("Payees will be saved automatically when you write checks, or you can add them manually.")
        self.empty_page.set_vexpand(True)

        self.stack = Gtk.Stack()
        self.stack.add_named(self.list_box, "list")
        self.stack.add_named(self.empty_page, "empty")

        scrolled.set_child(self.stack)
        main_box.append(scrolled)

        self.set_child(main_box)

    def _on_search_changed(self, entry):
        self._search_query = entry.get_text()
        self.refresh()

    def refresh(self):
        while True:
            row = self.list_box.get_first_child()
            if not row:
                break
            self.list_box.remove(row)

        payees = self.db.get_payees(search=self._search_query if self._search_query else None)
        if not payees:
            self.stack.set_visible_child_name("empty")
            return

        self.stack.set_visible_child_name("list")
        for payee in payees:
            row = self._create_payee_row(payee)
            self.list_box.append(row)

    def _create_payee_row(self, payee: Payee) -> Adw.ActionRow:
        row = Adw.ActionRow()
        row.set_title(GLib.markup_escape_text(payee.name))

        sub_parts = []
        if payee.category:
            sub_parts.append(f"Category: {payee.category}")
        if payee.default_memo:
            sub_parts.append(f"Default Memo: {payee.default_memo}")
        row.set_subtitle(" • ".join(sub_parts) if sub_parts else "No details")

        # Edit button
        edit_btn = Gtk.Button(icon_name="document-edit-symbolic")
        edit_btn.set_valign(Gtk.Align.CENTER)
        edit_btn.add_css_class("flat")
        edit_btn.connect("clicked", lambda *_: self._on_edit_payee_clicked(payee))
        row.add_suffix(edit_btn)

        # Delete button
        del_btn = Gtk.Button(icon_name="user-trash-symbolic")
        del_btn.set_valign(Gtk.Align.CENTER)
        del_btn.add_css_class("flat")
        del_btn.connect("clicked", lambda *_: self._on_delete_payee_clicked(payee))
        row.add_suffix(del_btn)

        return row

    def _on_add_payee_clicked(self, button):
        def on_saved(payee):
            self.db.save_payee(payee)
            self.refresh()
            if self.show_toast_cb:
                self.show_toast_cb(f"Payee '{payee.name}' created")

        dlg = PayeeEditDialog(self.get_root(), None, on_saved=on_saved)
        dlg.present()

    def _on_edit_payee_clicked(self, payee: Payee):
        def on_saved(updated_payee):
            self.db.save_payee(updated_payee)
            self.refresh()
            if self.show_toast_cb:
                self.show_toast_cb(f"Payee '{updated_payee.name}' updated")

        dlg = PayeeEditDialog(self.get_root(), payee, on_saved=on_saved)
        dlg.present()

    def _on_delete_payee_clicked(self, payee: Payee):
        self.db.delete_payee(payee.id)
        self.refresh()
        if self.show_toast_cb:
            self.show_toast_cb(f"Payee '{payee.name}' deleted")
