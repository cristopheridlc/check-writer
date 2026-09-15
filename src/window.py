# src/window.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gtk, Gio, GLib, GObject

from .core.database import CheckbookDatabase
from .core.models import Check
from .ui.writer_view import WriterView
from .ui.register_view import RegisterView
from .ui.payees_view import PayeesView
from .ui.preferences_dialog import PreferencesDialog


@Gtk.Template(resource_path='/com/example/CheckWriter/window.ui')
class CheckWriterWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'CheckWriterWindow'

    toast_overlay = Gtk.Template.Child()
    toolbar_view = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    view_switcher_title = Gtk.Template.Child()
    view_stack = Gtk.Template.Child()
    view_switcher_bar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.db = CheckbookDatabase()

        # Connect switcher title to switcher bar for mobile/adaptive layout
        self.view_switcher_title.bind_property(
            "title-visible",
            self.view_switcher_bar,
            "reveal",
            GObject.BindingFlags.SYNC_CREATE
        )

        # 1. Initialize Views
        self.writer_view = WriterView(
            db=self.db,
            on_check_saved=self._on_check_saved,
            show_toast_cb=self.show_toast
        )
        self.register_view = RegisterView(
            db=self.db,
            on_duplicate_check=self._on_duplicate_check,
            show_toast_cb=self.show_toast
        )
        self.payees_view = PayeesView(
            db=self.db,
            show_toast_cb=self.show_toast
        )

        # 2. Add Views to ViewStack
        page_writer = self.view_stack.add_titled_with_icon(
            self.writer_view,
            "writer",
            "Writer",
            "document-edit-symbolic"
        )
        page_register = self.view_stack.add_titled_with_icon(
            self.register_view,
            "register",
            "Register",
            "emblem-documents-symbolic"
        )
        page_payees = self.view_stack.add_titled_with_icon(
            self.payees_view,
            "payees",
            "Payees",
            "system-users-symbolic"
        )

        self._setup_actions()

    def _setup_actions(self):
        """Setup window-level actions and shortcuts."""
        # Shortcut overlay action
        shortcut_action = Gio.SimpleAction.new("show-help-overlay", None)
        shortcut_action.connect("activate", self._on_show_help_overlay)
        self.add_action(shortcut_action)

        # Save check action
        save_action = Gio.SimpleAction.new("save-check", None)
        save_action.connect("activate", lambda *_: self.writer_view._on_save_clicked(None))
        self.add_action(save_action)

        # Print check action
        print_action = Gio.SimpleAction.new("print-check", None)
        print_action.connect("activate", lambda *_: self.writer_view._on_print_clicked(None))
        self.add_action(print_action)

        # New check action
        new_action = Gio.SimpleAction.new("new-check", None)
        new_action.connect("activate", lambda *_: self.writer_view._on_new_check_clicked(None))
        self.add_action(new_action)

    def _on_show_help_overlay(self, action, param):
        builder = Gtk.Builder.new_from_resource("/com/example/CheckWriter/gtk/help-overlay.ui")
        help_overlay = builder.get_object("help_overlay")
        help_overlay.set_transient_for(self)
        help_overlay.present()

    def _on_check_saved(self, check: Check):
        self.register_view.refresh()
        self.payees_view.refresh()

    def _on_duplicate_check(self, check: Check):
        self.writer_view.load_check_for_editing(check)
        self.view_stack.set_visible_child_name("writer")
        self.show_toast(f"Loaded Check #{check.check_number} into Writer")

    def show_toast(self, message: str, timeout: int = 3):
        toast = Adw.Toast.new(message)
        toast.set_timeout(timeout)
        self.toast_overlay.add_toast(toast)

    def open_preferences(self):
        pref_dlg = PreferencesDialog(
            parent_window=self,
            db=self.db,
            on_saved=self._on_preferences_saved
        )
        pref_dlg.present()

    def _on_preferences_saved(self):
        self.writer_view._update_preview()
        self.writer_view._load_accounts()
        self.register_view.refresh()
        self.show_toast("Preferences updated")
