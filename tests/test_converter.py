# tests/test_converter.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from decimal import Decimal
from src.core.converter import number_to_words, amount_to_words


class TestNumberToWords(unittest.TestCase):

    def test_basic_units(self):
        self.assertEqual(number_to_words(0), "Zero")
        self.assertEqual(number_to_words(1), "One")
        self.assertEqual(number_to_words(7), "Seven")
        self.assertEqual(number_to_words(9), "Nine")

    def test_teens_and_tens(self):
        self.assertEqual(number_to_words(10), "Ten")
        self.assertEqual(number_to_words(14), "Fourteen")
        self.assertEqual(number_to_words(20), "Twenty")
        self.assertEqual(number_to_words(25), "Twenty-Five")
        self.assertEqual(number_to_words(99), "Ninety-Nine")

    def test_hundreds(self):
        self.assertEqual(number_to_words(100), "One Hundred")
        self.assertEqual(number_to_words(105), "One Hundred Five")
        self.assertEqual(number_to_words(342), "Three Hundred Forty-Two")

    def test_thousands_and_millions(self):
        self.assertEqual(number_to_words(1000), "One Thousand")
        self.assertEqual(number_to_words(1234), "One Thousand, Two Hundred Thirty-Four")
        self.assertEqual(number_to_words(1000000), "One Million")
        self.assertEqual(number_to_words(5000200), "Five Million, Two Hundred")

    def test_negative_numbers(self):
        self.assertEqual(number_to_words(-50), "Negative Fifty")


class TestAmountToWords(unittest.TestCase):

    def test_standard_amounts(self):
        self.assertEqual(
            amount_to_words(0.00),
            "Zero and 00/100 Dollars"
        )
        self.assertEqual(
            amount_to_words(123.45),
            "One Hundred Twenty-Three and 45/100 Dollars"
        )
        self.assertEqual(
            amount_to_words("1,234.56"),
            "One Thousand, Two Hundred Thirty-Four and 56/100 Dollars"
        )
        self.assertEqual(
            amount_to_words(1000),
            "One Thousand and 00/100 Dollars"
        )

    def test_security_fill(self):
        self.assertEqual(
            amount_to_words(50.00, security_fill=True),
            "*** Fifty and 00/100 Dollars ***"
        )

    def test_casing_options(self):
        self.assertEqual(
            amount_to_words(15.20, casing="UPPERCASE"),
            "FIFTEEN AND 20/100 DOLLARS"
        )
        self.assertEqual(
            amount_to_words(15.20, casing="lowercase"),
            "fifteen and 20/100 dollars"
        )

    def test_cents_in_words(self):
        self.assertEqual(
            amount_to_words(10.25, cents_format="words"),
            "Ten Dollars and Twenty-Five Cents"
        )

    def test_invalid_input(self):
        self.assertEqual(amount_to_words("not_a_number"), "Invalid Amount")


if __name__ == "__main__":
    unittest.main()
