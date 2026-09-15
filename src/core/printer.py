# src/core/printer.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import math
import cairo
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from .models import Account, Check, PrintSettings


# Standard dimensions in Points (72 points = 1 inch)
PERSONAL_CHECK_WIDTH_PT = 6.0 * 72    # 432 pt
PERSONAL_CHECK_HEIGHT_PT = 2.75 * 72  # 198 pt

BUSINESS_CHECK_WIDTH_PT = 8.5 * 72   # 612 pt
BUSINESS_CHECK_HEIGHT_PT = 3.5 * 72  # 252 pt

LETTER_PAGE_WIDTH_PT = 8.5 * 72      # 612 pt
LETTER_PAGE_HEIGHT_PT = 11.0 * 72    # 792 pt


class CheckRenderer:
    """Cairo vector rendering engine for bank checks."""

    @staticmethod
    def draw_check(
        cr: cairo.Context,
        check: Check,
        account: Account,
        width: float,
        height: float,
        is_preview: bool = False,
        settings: PrintSettings = None,
        draw_background: bool = True
    ) -> None:
        """Draw a single personal/business check into a Cairo context."""
        settings = settings or PrintSettings()

        # Save state
        cr.save()

        # Check background styling
        if draw_background:
            # Soft elegant gradient/tint for realistic check appearance
            pat = cairo.LinearGradient(0, 0, width, height)
            if is_preview:
                pat.add_color_stop_rgb(0, 0.95, 0.97, 0.99)
                pat.add_color_stop_rgb(1, 0.90, 0.94, 0.97)
            else:
                pat.add_color_stop_rgb(0, 0.98, 0.99, 1.0)
                pat.add_color_stop_rgb(1, 0.95, 0.97, 0.99)
            cr.rectangle(0, 0, width, height)
            cr.set_source(pat)
            cr.fill()

            # Outer subtle border / guilloche frame
            cr.set_source_rgb(0.70, 0.75, 0.80)
            cr.set_line_width(1.0)
            cr.rectangle(6, 6, width - 12, height - 12)
            cr.stroke()

            # Inner border
            cr.set_source_rgb(0.80, 0.85, 0.90)
            cr.set_line_width(0.5)
            cr.rectangle(8, 8, width - 16, height - 16)
            cr.stroke()

        # Text and Line colors
        text_color = (0.1, 0.1, 0.12)
        line_color = (0.45, 0.50, 0.55)
        accent_color = (0.15, 0.25, 0.40)

        # 1. Payor Information (Top Left)
        if settings.print_payor_info:
            cr.set_source_rgb(*text_color)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(10.0)
            cr.move_to(20, 25)
            cr.show_text(account.payor_name or "Jane Doe")

            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(8.0)
            cr.set_source_rgb(0.3, 0.3, 0.35)
            y_offset = 36
            if account.payor_address1:
                cr.move_to(20, y_offset)
                cr.show_text(account.payor_address1)
                y_offset += 11
            if account.payor_address2:
                cr.move_to(20, y_offset)
                cr.show_text(account.payor_address2)
                y_offset += 11
            if account.payor_phone:
                cr.move_to(20, y_offset)
                cr.show_text(account.payor_phone)

        # 2. Check Number (Top Right)
        cr.set_source_rgb(*accent_color)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(14.0)
        chk_num_str = str(check.check_number)
        x_bearing, y_bearing, t_w, t_h, x_advance, y_advance = cr.text_extents(chk_num_str)
        cr.move_to(width - 25 - t_w, 28)
        cr.show_text(chk_num_str)

        # 3. Bank Information (Top Center)
        if settings.print_bank_info and account.bank_name:
            cr.set_source_rgb(0.3, 0.3, 0.35)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(8.5)
            b_w = cr.text_extents(account.bank_name)[2]
            cr.move_to((width - b_w) / 2, 28)
            cr.show_text(account.bank_name)

        # 4. Date Line (Top Right below Check Number)
        date_line_x = width - 170
        date_line_w = 145
        date_y = 52

        cr.set_source_rgb(*text_color)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(7.5)
        cr.move_to(date_line_x - 30, date_y)
        cr.show_text("DATE")

        # Date underline
        cr.set_source_rgb(*line_color)
        cr.set_line_width(0.75)
        cr.move_to(date_line_x, date_y + 2)
        cr.line_to(date_line_x + date_line_w, date_y + 2)
        cr.stroke()

        # Date text
        if check.date_str:
            cr.set_source_rgb(*text_color)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(10.0)
            cr.move_to(date_line_x + 10, date_y)
            cr.show_text(check.date_str)

        # 5. Pay To The Order Of Line
        payee_y = 85
        payee_line_x = 90
        payee_line_w = width - payee_line_x - 145

        cr.set_source_rgb(*text_color)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(7.0)
        cr.move_to(20, payee_y - 8)
        cr.show_text("PAY TO THE")
        cr.move_to(20, payee_y)
        cr.show_text("ORDER OF")

        # Underline
        cr.set_source_rgb(*line_color)
        cr.set_line_width(0.75)
        cr.move_to(payee_line_x, payee_y + 2)
        cr.line_to(payee_line_x + payee_line_w, payee_y + 2)
        cr.stroke()

        # Payee text
        if check.payee:
            cr.set_source_rgb(*text_color)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(11.0)
            cr.move_to(payee_line_x + 8, payee_y - 1)
            cr.show_text(check.payee)

        # 6. Amount Box ($ [ 1,234.56 ])
        amt_box_x = width - 130
        amt_box_y = payee_y - 16
        amt_box_w = 105
        amt_box_h = 22

        # Dollar sign
        cr.set_source_rgb(*text_color)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(13.0)
        cr.move_to(amt_box_x - 14, amt_box_y + 16)
        cr.show_text("$")

        # Amount box border
        cr.set_source_rgb(0.70, 0.75, 0.80)
        cr.set_line_width(1.0)
        cr.rectangle(amt_box_x, amt_box_y, amt_box_w, amt_box_h)
        cr.stroke()

        # Amount value
        if check.amount > 0 or check.amount_words:
            cr.set_source_rgb(*text_color)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(12.0)
            amt_formatted = f"***{check.amount:,.2f}" if settings.security_fill else f"{check.amount:,.2f}"
            cr.move_to(amt_box_x + 8, amt_box_y + 16)
            cr.show_text(amt_formatted)

        # 7. Legal Words Amount Line
        words_y = 118
        words_line_x = 20
        words_line_w = width - 75

        # Underline
        cr.set_source_rgb(*line_color)
        cr.set_line_width(0.75)
        cr.move_to(words_line_x, words_y + 2)
        cr.line_to(words_line_x + words_line_w, words_y + 2)
        cr.stroke()

        # "DOLLARS" label at right
        cr.set_source_rgb(*text_color)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(7.5)
        cr.move_to(words_line_x + words_line_w + 6, words_y)
        cr.show_text("DOLLARS")

        # Words text with security filler line
        if check.amount_words:
            cr.set_source_rgb(*text_color)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(9.5)
            words_text = check.amount_words
            w_ext = cr.text_extents(words_text)[2]

            cr.move_to(words_line_x + 5, words_y - 1)
            cr.show_text(words_text)

            # Security trailing dash line if space allows
            start_dash_x = words_line_x + 10 + w_ext
            end_dash_x = words_line_x + words_line_w - 5
            if end_dash_x > start_dash_x + 20:
                cr.set_source_rgb(0.65, 0.70, 0.75)
                cr.set_line_width(0.75)
                cr.set_dash([4.0, 3.0])
                cr.move_to(start_dash_x, words_y - 4)
                cr.line_to(end_dash_x, words_y - 4)
                cr.stroke()
                cr.set_dash([])  # reset dash

        # 8. Memo Line (Bottom Left)
        memo_y = height - 42
        memo_line_x = 55
        memo_line_w = (width / 2) - 65

        cr.set_source_rgb(*text_color)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(7.5)
        cr.move_to(20, memo_y)
        cr.show_text("MEMO")

        cr.set_source_rgb(*line_color)
        cr.set_line_width(0.75)
        cr.move_to(memo_line_x, memo_y + 2)
        cr.line_to(memo_line_x + memo_line_w, memo_y + 2)
        cr.stroke()

        if check.memo:
            cr.set_source_rgb(*text_color)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(9.0)
            cr.move_to(memo_line_x + 5, memo_y)
            cr.show_text(check.memo)

        # 9. Signature Line (Bottom Right)
        sig_y = height - 42
        sig_line_x = width - 190
        sig_line_w = 165

        cr.set_source_rgb(*line_color)
        cr.set_line_width(0.75)
        cr.move_to(sig_line_x, sig_y + 2)
        cr.line_to(sig_line_x + sig_line_w, sig_y + 2)
        cr.stroke()

        cr.set_source_rgb(0.4, 0.4, 0.45)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(6.5)
        lbl = "AUTHORIZED SIGNATURE"
        lbl_w = cr.text_extents(lbl)[2]
        cr.move_to(sig_line_x + (sig_line_w - lbl_w) / 2, sig_y + 10)
        cr.show_text(lbl)

        # 10. MICR Routing/Account Encoding Line (Bottom)
        if settings.print_micr and (account.routing_number or account.account_number):
            micr_y = height - 12
            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(10.0)

            # Standard MICR symbol approximations: Transit '⑆' -> 'A', On-Us '⑈' -> 'C'
            micr_line = f"A{account.routing_number}A   {account.account_number}C   {check.check_number}"
            m_w = cr.text_extents(micr_line)[2]
            cr.move_to((width - m_w) / 2, micr_y)
            cr.show_text(micr_line)

        # 11. VOID Watermark if check is voided
        if check.status.lower() == "voided":
            cr.save()
            cr.translate(width / 2, height / 2)
            cr.rotate(-math.pi / 8)
            cr.set_source_rgba(0.9, 0.2, 0.2, 0.35)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(52.0)
            void_ext = cr.text_extents("VOID")[2]
            cr.move_to(-void_ext / 2, 18)
            cr.show_text("VOID")
            cr.restore()

        cr.restore()

    @staticmethod
    def draw_voucher_stub(
        cr: cairo.Context,
        check: Check,
        account: Account,
        x: float,
        y: float,
        width: float,
        height: float,
        stub_title: str = "TRANSACTION RECORD"
    ) -> None:
        """Draw a voucher record stub with transaction table."""
        cr.save()
        cr.translate(x, y)

        # Perforation dashed line at top
        cr.set_source_rgb(0.7, 0.7, 0.75)
        cr.set_line_width(0.75)
        cr.set_dash([3.0, 3.0])
        cr.move_to(0, 0)
        cr.line_to(width, 0)
        cr.stroke()
        cr.set_dash([])

        # Header box
        cr.set_source_rgb(0.2, 0.25, 0.35)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(9.0)
        cr.move_to(20, 20)
        cr.show_text(stub_title)

        cr.set_font_size(8.0)
        cr.move_to(width - 150, 20)
        cr.show_text(f"CHECK #{check.check_number}")

        # Table Grid
        table_y = 35
        table_h = 75
        cr.set_source_rgb(0.85, 0.88, 0.92)
        cr.set_line_width(0.75)
        cr.rectangle(20, table_y, width - 40, table_h)
        cr.stroke()

        # Header bar
        cr.set_source_rgb(0.92, 0.94, 0.97)
        cr.rectangle(20, table_y, width - 40, 18)
        cr.fill()

        # Column headers
        cr.set_source_rgb(0.2, 0.25, 0.35)
        cr.set_font_size(7.5)
        cr.move_to(30, table_y + 12)
        cr.show_text("DATE")
        cr.move_to(110, table_y + 12)
        cr.show_text("PAYEE")
        cr.move_to(310, table_y + 12)
        cr.show_text("MEMO / DESCRIPTION")
        cr.move_to(width - 110, table_y + 12)
        cr.show_text("AMOUNT")

        # Values
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(8.5)
        cr.move_to(30, table_y + 35)
        cr.show_text(check.date_str)
        cr.move_to(110, table_y + 35)
        cr.show_text(check.payee[:28])
        cr.move_to(310, table_y + 35)
        cr.show_text(check.memo[:30])
        cr.move_to(width - 110, table_y + 35)
        cr.show_text(f"${check.amount:,.2f}")

        cr.restore()

    @staticmethod
    def draw_full_page(
        cr: cairo.Context,
        check: Check,
        account: Account,
        settings: PrintSettings,
        page_width: float = LETTER_PAGE_WIDTH_PT,
        page_height: float = LETTER_PAGE_HEIGHT_PT,
    ) -> None:
        """Render complete page according to layout setting."""
        # Convert mm offsets to points (1 mm = 2.83465 pt)
        offset_x_pt = settings.offset_x_mm * 2.83465
        offset_y_pt = settings.offset_y_mm * 2.83465

        cr.save()
        cr.translate(offset_x_pt, offset_y_pt)

        if settings.layout == "voucher_top":
            # Top check: 8.5" x 3.5" (612 x 252 pt)
            cr.save()
            CheckRenderer.draw_check(
                cr, check, account,
                width=page_width,
                height=252,
                is_preview=False,
                settings=settings,
                draw_background=False
            )
            cr.restore()

            # Stub 1 (Middle)
            CheckRenderer.draw_voucher_stub(
                cr, check, account,
                x=0, y=260,
                width=page_width, height=240,
                stub_title="PAYEE VOUCHER RECORD"
            )

            # Stub 2 (Bottom)
            CheckRenderer.draw_voucher_stub(
                cr, check, account,
                x=0, y=520,
                width=page_width, height=240,
                stub_title="PAYOR FILE COPY"
            )

        elif settings.layout == "three_per_page":
            # 3 checks per letter page (each 3.5" tall with margins)
            check_h = 252
            pos_y = settings.page_position * check_h + 10
            cr.save()
            cr.translate(0, pos_y)
            CheckRenderer.draw_check(
                cr, check, account,
                width=page_width,
                height=check_h - 10,
                is_preview=False,
                settings=settings,
                draw_background=False
            )
            cr.restore()

        else:  # 'personal_single' (standard single check)
            cr.save()
            CheckRenderer.draw_check(
                cr, check, account,
                width=PERSONAL_CHECK_WIDTH_PT,
                height=PERSONAL_CHECK_HEIGHT_PT,
                is_preview=False,
                settings=settings,
                draw_background=False
            )
            cr.restore()

        cr.restore()


class CheckPrintManager:
    """Manages Gtk.PrintOperation for check printing."""

    def __init__(self, parent_window: Gtk.Window):
        self.parent_window = parent_window

    def print_check(self, check: Check, account: Account, settings: PrintSettings) -> None:
        print_op = Gtk.PrintOperation()
        print_op.set_job_name(f"Check #{check.check_number} - {check.payee}")
        print_op.set_n_pages(1)

        def on_draw_page(operation, context, page_nr):
            cr = context.get_cairo_context()
            page_setup = context.get_page_setup()
            width_pt = page_setup.get_page_width(Gtk.Unit.POINTS)
            height_pt = page_setup.get_page_height(Gtk.Unit.POINTS)

            CheckRenderer.draw_full_page(
                cr=cr,
                check=check,
                account=account,
                settings=settings,
                page_width=width_pt,
                page_height=height_pt
            )

        print_op.connect("draw-page", on_draw_page)
        print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self.parent_window)

    def export_pdf(self, file_path: str, check: Check, account: Account, settings: PrintSettings) -> None:
        """Export the check directly to a PDF file."""
        if settings.layout == "personal_single":
            w, h = PERSONAL_CHECK_WIDTH_PT, PERSONAL_CHECK_HEIGHT_PT
        else:
            w, h = LETTER_PAGE_WIDTH_PT, LETTER_PAGE_HEIGHT_PT

        surface = cairo.PDFSurface(file_path, w, h)
        cr = cairo.Context(surface)
        CheckRenderer.draw_full_page(cr, check, account, settings, w, h)
        surface.show_page()
        surface.finish()
