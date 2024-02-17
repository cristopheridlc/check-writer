# window.py
#
# Copyright 2024 Cristopher De La Cruz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk

def number_to_words(amount):
    if amount < 0:
        return "Negative " + number_to_words(-amount)

    if amount == 0:
        return "Zero"

    words = ""
    units = [
        "", "One", "Two", "Three", "Four",
        "Five", "Six", "Seven", "Eight", "Nine"
    ]
    teens = [
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen",
        "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"
    ]
    tens = [
        "", "", "Twenty", "Thirty", "Forty",
        "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
    ]
    thousands = [
        "", "Thousand", "Million", "Billion", "Trillion",
        "Quadrillion", "Quintillion", "Sextillion", "Septillion",
        "Octillion", "Nonillion", "Decillion"
    ]

    def parse_hundred(hundred):
        result = ""
        if hundred > 99:
            result += units[hundred // 100] + " Hundred "
            hundred %= 100
        if hundred > 19:
            result += tens[hundred // 10] + " "
            hundred %= 10
        if 0 < hundred < 10:
            result += units[hundred] + " "
        elif hundred >= 10:
            result += teens[hundred - 10] + " "
        return result

    def parse_group(number, index):
        return "" if number == 0 else number_to_words(number) + " " + thousands[index] + ", "

    i = 0
    while amount >= 1000:
        words = parse_group(amount % 1000, i) + words
        amount //= 1000
        i += 1
    words = parse_hundred(amount) + words

    return words.strip().rstrip(',')

@Gtk.Template(resource_path='/com/example/CheckWriter/window.ui')
class CheckWriterWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'CheckWriterWindow'

    amount_entry = Gtk.Template.Child()
    convert_button = Gtk.Template.Child()
    result_label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.convert_button.connect("clicked", self.on_convert_clicked)

    def on_convert_clicked(self, button):
        amount_str = self.amount_entry.get_text()
        try:
            amount = float(amount_str)
            amount_in_words = number_to_words(int(amount))
            cents = int((amount - int(amount)) * 100)
            result_text = f"{amount_in_words} and {cents:02d}/100 dollars"
        except ValueError:
            result_text = "Please enter a valid number"
        self.result_label.set_text(result_text)

