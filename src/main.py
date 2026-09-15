# src/main.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import CheckWriterWindow


class CheckWriterApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='com.example.CheckWriter',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action, ['<primary>comma'])

    def do_activate(self):
        """Called when the application is activated."""
        win = self.props.active_window
        if not win:
            win = CheckWriterWindow(application=self)
            self.set_accels_for_action("win.new-check", ["<primary>n"])
            self.set_accels_for_action("win.save-check", ["<primary>s"])
            self.set_accels_for_action("win.print-check", ["<primary>p"])
            self.set_accels_for_action("win.show-help-overlay", ["<primary>question"])
        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name='Check Writer',
            application_icon='com.example.CheckWriter',
            developer_name='Cristopher De La Cruz',
            version='1.0.0',
            developers=['Cristopher De La Cruz'],
            copyright='© 2024-2026 Cristopher De La Cruz',
            license_type=Gtk.License.GPL_3_0,
            comments='A modern GNOME application for writing, previewing, printing, and tracking checks.'
        )
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        win = self.props.active_window
        if win and hasattr(win, 'open_preferences'):
            win.open_preferences()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action."""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version=None):
    """The application's entry point."""
    app = CheckWriterApplication()
    return app.run(sys.argv)
