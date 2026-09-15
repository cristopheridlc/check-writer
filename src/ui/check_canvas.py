# src/ui/check_canvas.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from ..core.models import Account, Check, PrintSettings
from ..core.printer import CheckRenderer, PERSONAL_CHECK_WIDTH_PT, PERSONAL_CHECK_HEIGHT_PT


class CheckCanvas(Gtk.DrawingArea):
    """Interactive Cairo-based check preview canvas."""

    def __init__(self, check: Check = None, account: Account = None, settings: PrintSettings = None):
        super().__init__()
        self._check = check or Check()
        self._account = account or Account()
        self._settings = settings or PrintSettings()

        self.set_draw_func(self._on_draw)
        self.set_content_width(500)
        self.set_content_height(230)
        self.set_hexpand(True)
        self.set_vexpand(False)

    def update(self, check: Check, account: Account, settings: PrintSettings = None):
        """Update check data and redraw canvas."""
        self._check = check
        self._account = account
        if settings:
            self._settings = settings
        self.queue_draw()

    def _on_draw(self, area, cr, width, height):
        # Calculate aspect ratio scaling to fit comfortably within the widget
        base_w = PERSONAL_CHECK_WIDTH_PT
        base_h = PERSONAL_CHECK_HEIGHT_PT

        # Add 12px padding around the check
        avail_w = max(width - 24, 10)
        avail_h = max(height - 24, 10)

        scale_x = avail_w / base_w
        scale_y = avail_h / base_h
        scale = min(scale_x, scale_y)

        # Center the check in the available canvas
        check_w = base_w * scale
        check_h = base_h * scale
        offset_x = (width - check_w) / 2
        offset_y = (height - check_h) / 2

        cr.save()
        cr.translate(offset_x, offset_y)
        cr.scale(scale, scale)

        # Draw realistic shadow behind the check
        cr.save()
        cr.set_source_rgba(0, 0, 0, 0.08)
        cr.rectangle(4, 4, base_w, base_h)
        cr.fill()
        cr.restore()

        CheckRenderer.draw_check(
            cr=cr,
            check=self._check,
            account=self._account,
            width=base_w,
            height=base_h,
            is_preview=True,
            settings=self._settings,
            draw_background=True
        )

        cr.restore()
