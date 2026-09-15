# tests/test_printer.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import tempfile
import unittest
import cairo

from src.core.models import Account, Check, PrintSettings
from src.core.printer import CheckRenderer, CheckPrintManager, PERSONAL_CHECK_WIDTH_PT, PERSONAL_CHECK_HEIGHT_PT


class TestPrinter(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.account = Account(
            name="Checking",
            bank_name="Test Bank",
            routing_number="123456789",
            account_number="987654321",
            payor_name="Alice Smith",
            payor_address1="456 Elm St",
            payor_address2="Metropolis, NY 10001"
        )
        self.check = Check(
            check_number=2001,
            date_str="2026-09-15",
            payee="Bob Johnson",
            amount=250.75,
            amount_words="Two Hundred Fifty and 75/100 Dollars",
            memo="Design Services",
            status="issued"
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_cairo_image_render(self):
        """Verify Cairo renders onto an ImageSurface without throwing errors."""
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 300)
        cr = cairo.Context(surface)
        settings = PrintSettings()
        CheckRenderer.draw_check(
            cr=cr,
            check=self.check,
            account=self.account,
            width=PERSONAL_CHECK_WIDTH_PT,
            height=PERSONAL_CHECK_HEIGHT_PT,
            is_preview=True,
            settings=settings
        )
        surface.flush()
        self.assertEqual(surface.get_width(), 600)

    def test_export_pdf_generation(self):
        """Verify direct PDF file export produces a valid PDF file."""
        pdf_path = os.path.join(self.tmp_dir.name, "check_test.pdf")
        settings = PrintSettings(layout="personal_single")

        surface = cairo.PDFSurface(pdf_path, PERSONAL_CHECK_WIDTH_PT, PERSONAL_CHECK_HEIGHT_PT)
        cr = cairo.Context(surface)
        CheckRenderer.draw_full_page(cr, self.check, self.account, settings, PERSONAL_CHECK_WIDTH_PT, PERSONAL_CHECK_HEIGHT_PT)
        surface.show_page()
        surface.finish()

        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 500)

    def test_export_voucher_pdf(self):
        """Verify voucher (check + 2 stubs) PDF export."""
        pdf_path = os.path.join(self.tmp_dir.name, "voucher_test.pdf")
        settings = PrintSettings(layout="voucher_top")

        surface = cairo.PDFSurface(pdf_path, 612, 792)
        cr = cairo.Context(surface)
        CheckRenderer.draw_full_page(cr, self.check, self.account, settings, 612, 792)
        surface.show_page()
        surface.finish()

        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)


if __name__ == "__main__":
    unittest.main()
