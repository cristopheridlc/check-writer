# src/ui/writer_view.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import date, datetime
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, Gio, GLib

from ..core.models import Account, Check, PrintSettings
from ..core.converter import amount_to_words
from ..core.database import CheckbookDatabase
from ..core.printer import CheckPrintManager
from .check_canvas import CheckCanvas


class WriterView(Adw.Bin):
    """The interactive Check Writer form and live preview screen."""

    def __init__(self, db: CheckbookDatabase, on_check_saved=None, show_toast_cb=None):
        super().__init__()
        self.db = db
        self.on_check_saved = on_check_saved
        self.show_toast_cb = show_toast_cb

        self.current_account: Account = self.db.get_default_account()
        self.current_check = Check(
            account_id=self.current_account.id,
            check_number=self.current_account.next_check_number,
            date_str=date.today().strftime("%Y-%m-%d")
        )
        self.print_settings = PrintSettings()
        self._load_settings()

        self._build_ui()
        self._load_accounts()
        self._load_payee_completion()
        self._update_preview()

    def _load_settings(self):
        self.print_settings.layout = self.db.get_setting("layout", "personal_single")
        self.print_settings.offset_x_mm = float(self.db.get_setting("offset_x_mm", "0.0") or 0.0)
        self.print_settings.offset_y_mm = float(self.db.get_setting("offset_y_mm", "0.0") or 0.0)
        self.print_settings.security_fill = (self.db.get_setting("security_fill", "true").lower() == "true")
        self.print_settings.casing = self.db.get_setting("casing", "Title")

    def _build_ui(self):
        # Main scrollable container
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(920)
        clamp.set_tightening_threshold(650)
        clamp.set_margin_top(16)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)

        # 1. Live Check Canvas Preview Card
        preview_card = Gtk.Frame()
        preview_card.add_css_class("card")
        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        preview_box.set_margin_top(12)
        preview_box.set_margin_bottom(12)
        preview_box.set_margin_start(12)
        preview_box.set_margin_end(12)

        preview_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        preview_title = Gtk.Label(label="<b>Live Check Preview</b>", use_markup=True, xalign=0)
        preview_title.set_hexpand(True)
        preview_header.append(preview_title)

        copy_words_btn = Gtk.Button(icon_name="edit-copy-symbolic", tooltip_text="Copy Words to Clipboard")
        copy_words_btn.add_css_class("flat")
        copy_words_btn.connect("clicked", self._on_copy_words_clicked)
        preview_header.append(copy_words_btn)

        self.canvas = CheckCanvas(self.current_check, self.current_account, self.print_settings)
        preview_box.append(preview_header)
        preview_box.append(self.canvas)
        preview_card.set_child(preview_box)
        main_box.append(preview_card)

        # 2. Form Preferences Group
        form_group = Adw.PreferencesGroup()
        form_group.set_title("Check Details")
        form_group.set_description("Fill in check information. The preview and legal amount words update in real-time.")

        # Account Selector Row
        self.account_row = Adw.ComboRow(title="Bank Account")
        self.account_row.connect("notify::selected", self._on_account_changed)
        form_group.add(self.account_row)

        # Check Number & Date Row (EntryRow)
        self.check_num_row = Adw.EntryRow(title="Check Number")
        self.check_num_row.set_text(str(self.current_check.check_number))
        self.check_num_row.connect("changed", self._on_form_changed)
        form_group.add(self.check_num_row)

        # Date Row with Today button
        self.date_row = Adw.EntryRow(title="Date (YYYY-MM-DD)")
        self.date_row.set_text(self.current_check.date_str)
        self.date_row.connect("changed", self._on_form_changed)
        
        today_btn = Gtk.Button(label="Today")
        today_btn.set_valign(Gtk.Align.CENTER)
        today_btn.add_css_class("flat")
        today_btn.connect("clicked", lambda _: self.date_row.set_text(date.today().strftime("%Y-%m-%d")))
        self.date_row.add_suffix(today_btn)
        form_group.add(self.date_row)

        # Payee Entry Row
        self.payee_row = Adw.EntryRow(title="Pay to the Order of")
        self.payee_row.connect("changed", self._on_payee_changed)
        form_group.add(self.payee_row)

        # Amount Entry Row
        self.amount_row = Adw.EntryRow(title="Amount ($)")
        self.amount_row.set_text("0.00")
        self.amount_row.connect("changed", self._on_amount_changed)
        form_group.add(self.amount_row)

        # Legal Amount Words (Expanded Info Row)
        self.words_row = Adw.ActionRow(title="Legal Amount in Words")
        self.words_label = Gtk.Label(label="", xalign=1, wrap=True)
        self.words_label.add_css_class("dim-label")
        self.words_label.add_css_class("numeric")
        self.words_row.add_suffix(self.words_label)
        form_group.add(self.words_row)

        # Memo Entry Row
        self.memo_row = Adw.EntryRow(title="Memo")
        self.memo_row.connect("changed", self._on_form_changed)
        form_group.add(self.memo_row)

        main_box.append(form_group)

        # 3. Primary Actions Bar
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        actions_box.set_halign(Gtk.Align.CENTER)
        actions_box.set_margin_top(8)

        # Save Button
        save_btn = Gtk.Button(label="Save to Register")
        save_btn.set_icon_name("document-save-symbolic")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save_clicked)
        actions_box.append(save_btn)

        # Print Button
        print_btn = Gtk.Button(label="Print Check")
        print_btn.set_icon_name("printer-symbolic")
        print_btn.add_css_class("accent")
        print_btn.connect("clicked", self._on_print_clicked)
        actions_box.append(print_btn)

        # Export PDF Button
        pdf_btn = Gtk.Button(label="Export PDF")
        pdf_btn.set_icon_name("application-pdf-symbolic")
        pdf_btn.connect("clicked", self._on_export_pdf_clicked)
        actions_box.append(pdf_btn)

        # New / Clear Button
        new_btn = Gtk.Button(label="New Check")
        new_btn.set_icon_name("document-new-symbolic")
        new_btn.add_css_class("flat")
        new_btn.connect("clicked", self._on_new_check_clicked)
        actions_box.append(new_btn)

        main_box.append(actions_box)

        clamp.set_child(main_box)
        scrolled.set_child(clamp)
        self.set_child(scrolled)

    def _load_accounts(self):
        self.accounts = self.db.get_accounts()
        str_list = Gtk.StringList()
        default_idx = 0
        for i, acc in enumerate(self.accounts):
            str_list.append(f"{acc.name} ({acc.bank_name} ••••{acc.account_number[-4:] if len(acc.account_number) >= 4 else acc.account_number})")
            if acc.is_default:
                default_idx = i

        self.account_row.set_model(str_list)
        if self.accounts:
            self.account_row.set_selected(default_idx)
            self.current_account = self.accounts[default_idx]

    def _load_payee_completion(self):
        # We can populate payees for quick suggestions if needed
        pass

    def _on_account_changed(self, row, pspec):
        idx = row.get_selected()
        if 0 <= idx < len(self.accounts):
            self.current_account = self.accounts[idx]
            self.current_check.account_id = self.current_account.id
            self.check_num_row.set_text(str(self.current_account.next_check_number))
            self._update_preview()

    def _on_payee_changed(self, entry):
        payee_name = entry.get_text()
        # If matches a saved payee and memo is empty, autofill default memo
        if payee_name:
            payee = self.db.get_payee_by_name(payee_name)
            if payee and payee.default_memo and not self.memo_row.get_text():
                self.memo_row.set_text(payee.default_memo)
        self._on_form_changed(entry)

    def _on_amount_changed(self, entry):
        amt_str = entry.get_text().replace("$", "").replace(",", "").strip()
        try:
            amt = float(amt_str) if amt_str else 0.0
            words = amount_to_words(
                amount=amt,
                currency="Dollars",
                casing=self.print_settings.casing,
                security_fill=self.print_settings.security_fill
            )
            self.words_label.set_text(words)
            self.current_check.amount = amt
            self.current_check.amount_words = words
        except ValueError:
            self.words_label.set_text("Invalid Amount")
            self.current_check.amount_words = ""

        self._update_preview()

    def _on_form_changed(self, widget):
        try:
            num_str = self.check_num_row.get_text().strip()
            self.current_check.check_number = int(num_str) if num_str.isdigit() else 1001
        except Exception:
            self.current_check.check_number = 1001

        self.current_check.date_str = self.date_row.get_text().strip()
        self.current_check.payee = self.payee_row.get_text().strip()
        self.current_check.memo = self.memo_row.get_text().strip()

        self._update_preview()

    def _update_preview(self):
        self._load_settings()
        self.canvas.update(self.current_check, self.current_account, self.print_settings)

    def _on_copy_words_clicked(self, button):
        words = self.current_check.amount_words
        if words:
            clipboard = Gdk.Display.get_default().get_clipboard()
            clipboard.set(words)
            if self.show_toast_cb:
                self.show_toast_cb("Amount in words copied to clipboard")

    def _on_save_clicked(self, button):
        if not self.current_check.payee:
            if self.show_toast_cb:
                self.show_toast_cb("Please specify a payee before saving")
            return

        self._on_form_changed(None)
        check_id = self.db.save_check(self.current_check)
        self.current_check.id = check_id

        # Increment next check number on account
        if self.current_account and self.current_account.id:
            next_num = self.db.increment_next_check_number(self.current_account.id)
            self.current_account.next_check_number = next_num

        if self.show_toast_cb:
            self.show_toast_cb(f"Check #{self.current_check.check_number} saved to register")

        if self.on_check_saved:
            self.on_check_saved(self.current_check)

        # Prepare for next check
        self.check_num_row.set_text(str(self.current_account.next_check_number))

    def _on_print_clicked(self, button):
        self._on_form_changed(None)
        root = self.get_root()
        printer = CheckPrintManager(root)
        printer.print_check(self.current_check, self.current_account, self.print_settings)

    def _on_export_pdf_clicked(self, button):
        self._on_form_changed(None)
        root = self.get_root()
        dialog = Gtk.FileDialog()
        dialog.set_title("Export Check to PDF")
        dialog.set_initial_name(f"Check_{self.current_check.check_number}_{self.current_check.payee or 'Draft'}.pdf")

        def on_save_response(file_dialog, result):
            try:
                gfile = file_dialog.save_finish(result)
                if gfile:
                    file_path = gfile.get_path()
                    printer = CheckPrintManager(root)
                    printer.export_pdf(file_path, self.current_check, self.current_account, self.print_settings)
                    if self.show_toast_cb:
                        self.show_toast_cb(f"Check exported to PDF: {gfile.get_basename()}")
            except GLib.Error:
                pass  # User canceled

        dialog.save(root, None, on_save_response)

    def _on_new_check_clicked(self, button):
        self.current_check = Check(
            account_id=self.current_account.id if self.current_account else None,
            check_number=self.current_account.next_check_number if self.current_account else 1001,
            date_str=date.today().strftime("%Y-%m-%d")
        )
        self.check_num_row.set_text(str(self.current_check.check_number))
        self.date_row.set_text(self.current_check.date_str)
        self.payee_row.set_text("")
        self.amount_row.set_text("0.00")
        self.memo_row.set_text("")
        self._update_preview()

    def load_check_for_editing(self, check: Check):
        """Populate form with existing check for editing or duplication."""
        self.current_check = check
        self.check_num_row.set_text(str(check.check_number))
        self.date_row.set_text(check.date_str)
        self.payee_row.set_text(check.payee)
        self.amount_row.set_text(f"{check.amount:.2f}")
        self.memo_row.set_text(check.memo)
        self._update_preview()
