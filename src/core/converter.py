# src/core/converter.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

from decimal import Decimal, ROUND_HALF_UP
from typing import Union


UNITS = [
    "", "One", "Two", "Three", "Four",
    "Five", "Six", "Seven", "Eight", "Nine"
]

TEENS = [
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen",
    "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"
]

TENS = [
    "", "", "Twenty", "Thirty", "Forty",
    "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
]

SCALES = [
    "", "Thousand", "Million", "Billion", "Trillion", "Quadrillion"
]


def _parse_hundred(n: int) -> str:
    """Parse a number less than 1000 into words."""
    result = []
    hundreds = n // 100
    remainder = n % 100

    if hundreds > 0:
        result.append(f"{UNITS[hundreds]} Hundred")

    if remainder > 0:
        if remainder < 10:
            result.append(UNITS[remainder])
        elif remainder < 20:
            result.append(TEENS[remainder - 10])
        else:
            ten = remainder // 10
            unit = remainder % 10
            if unit > 0:
                result.append(f"{TENS[ten]}-{UNITS[unit]}")
            else:
                result.append(TENS[ten])

    return " ".join(result)


def number_to_words(number: int) -> str:
    """Convert an integer into English words."""
    if number == 0:
        return "Zero"

    if number < 0:
        return f"Negative {number_to_words(-number)}"

    groups = []
    scale_idx = 0
    num = number

    while num > 0:
        group_val = num % 1000
        if group_val != 0:
            group_words = _parse_hundred(group_val)
            scale_name = SCALES[scale_idx]
            if scale_name:
                groups.insert(0, f"{group_words} {scale_name}")
            else:
                groups.insert(0, group_words)
        num //= 1000
        scale_idx += 1
        if scale_idx >= len(SCALES):
            break

    return ", ".join(groups) if len(groups) > 1 else (groups[0] if groups else "Zero")


def amount_to_words(
    amount: Union[float, int, str, Decimal],
    currency: str = "Dollars",
    cents_label: str = "Cents",
    casing: str = "Title",
    security_fill: bool = False,
    cents_format: str = "fraction",  # 'fraction' (45/100), 'words' (Forty-Five Cents), 'none'
) -> str:
    """Convert a monetary amount to standard check legal wording.

    Examples:
        123.45 -> 'One Hundred Twenty-Three and 45/100 Dollars'
        1000.00 (with security_fill) -> '*** One Thousand and 00/100 Dollars ***'
    """
    try:
        if isinstance(amount, str):
            clean_str = amount.replace("$", "").replace(",", "").strip()
            dec_amount = Decimal(clean_str)
        else:
            dec_amount = Decimal(str(amount))
    except Exception:
        return "Invalid Amount"

    # Quantize to 2 decimal places with standard half-up rounding
    dec_amount = dec_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    is_negative = dec_amount < 0
    dec_amount = abs(dec_amount)

    dollars = int(dec_amount)
    cents = int((dec_amount - dollars) * 100)

    dollars_words = number_to_words(dollars)

    if cents_format == "fraction":
        cents_part = f"{cents:02d}/100"
        if currency:
            words = f"{dollars_words} and {cents_part} {currency}"
        else:
            words = f"{dollars_words} and {cents_part}"
    elif cents_format == "words":
        cents_words = number_to_words(cents)
        if cents > 0:
            words = f"{dollars_words} {currency} and {cents_words} {cents_label}"
        else:
            words = f"{dollars_words} {currency}"
    else:  # 'none'
        words = f"{dollars_words} {currency}" if currency else dollars_words

    if is_negative:
        words = f"Negative {words}"

    # Apply casing
    casing_lower = casing.lower()
    if casing_lower == "uppercase":
        words = words.upper()
    elif casing_lower == "lowercase":
        words = words.lower()
    elif casing_lower == "sentence":
        words = words.capitalize()
    # default is Title-style as constructed

    if security_fill:
        words = f"*** {words} ***"

    return words
