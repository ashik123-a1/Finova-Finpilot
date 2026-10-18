"""
Locale-Aware Formatting Engine for SME Finance Copilot.
Handles number formatting, decimal separators, native digit conversion,
currency presentation, and bidirectional (RTL/LTR) text direction.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from src.i18n.registry import LanguageRegistry, TextDirection


class LocaleFormatter:
    """Provides culturally and jurisdictionally compliant financial formatting."""

    # Decimal & Thousands Separators by Locale
    # (decimal_sep, thousands_sep)
    LOCALE_SEPARATORS: Dict[str, Tuple[str, str]] = {
        "en": (".", ","),
        "bn": (".", ","),
        "zh": (".", ","),
        "ar": (".", ","),
        "es": (",", "."),
        "fr": (",", " "),
        "de": (",", "."),
        "it": (",", "."),
        "pt": (",", "."),
        "ru": (",", " "),
        "hi": (".", ","),
        "ur": (".", ","),
        "id": (",", "."),
        "tr": (",", "."),
        "vi": (",", "."),
        "nl": (",", "."),
    }

    # Digit mapping tables
    BENGALI_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
    ARABIC_INDIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    DEVANAGARI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
    EASTERN_ARABIC_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

    # Reverse digit mapping tables to ASCII
    ASCII_FROM_ALL_DIGITS = str.maketrans(
        "০১২৩৪৫৬৭৮৯٠١٢٣٤٥٦٧٨٩०१२३४५६७८९۰۱۲۳۴۵۶۷۸۹",
        "0123456789012345678901234567890123456789"
    )

    @classmethod
    def normalize_digits_to_ascii(cls, text: str) -> str:
        """Converts any Unicode non-Latin numerals (Bengali, Arabic-Indic, Devanagari, etc.) to standard ASCII 0-9."""
        if not text:
            return ""
        return text.translate(cls.ASCII_FROM_ALL_DIGITS)

    @classmethod
    def convert_native_to_ascii(cls, text: str) -> str:
        """Alias for normalize_digits_to_ascii."""
        return cls.normalize_digits_to_ascii(text)

    @classmethod
    def convert_digits_to_native(cls, text: str, locale: str) -> str:
        """Converts ASCII digits in text to native numerals for the locale."""
        if not text:
            return ""
        lang = locale.lower().split("-")[0].strip()
        if lang == "bn":
            return text.translate(cls.BENGALI_DIGITS)
        elif lang in ("ar", "ur"):
            return text.translate(cls.ARABIC_INDIC_DIGITS)
        elif lang == "hi":
            return text.translate(cls.DEVANAGARI_DIGITS)
        elif lang == "fa":
            return text.translate(cls.EASTERN_ARABIC_DIGITS)
        return text

    @classmethod
    def format_number(
        cls,
        value: Decimal | int | float,
        locale: str = "en",
        decimal_places: int = 2,
        use_native_digits: bool = False
    ) -> str:
        """
        Formats a number with locale-appropriate decimal and thousands separators.
        Guarantees exact Decimal conversion without binary floating-point drift.
        """
        lang = locale.lower().split("-")[0].strip()
        dec_sep, thou_sep = cls.LOCALE_SEPARATORS.get(lang, (".", ","))

        if isinstance(value, float):
            d = Decimal(str(value))
        elif isinstance(value, int):
            d = Decimal(value)
        else:
            d = value

        # Split integer and fraction
        fmt = f"{{:,.{decimal_places}f}}"
        standard_str = fmt.format(d)  # e.g. "1,234.56"

        # Replace standard US separators with locale separators
        if "." in standard_str:
            int_part, frac_part = standard_str.split(".")
            int_part = int_part.replace(",", thou_sep)
            result = f"{int_part}{dec_sep}{frac_part}" if decimal_places > 0 else int_part
        else:
            result = standard_str.replace(",", thou_sep)

        if use_native_digits:
            if lang == "bn":
                result = result.translate(cls.BENGALI_DIGITS)
            elif lang in ("ar", "ur"):
                result = result.translate(cls.ARABIC_INDIC_DIGITS)
            elif lang == "hi":
                result = result.translate(cls.DEVANAGARI_DIGITS)

        return result

    @classmethod
    def format_currency(
        cls,
        amount_minor: int,
        currency: str = "BDT",
        locale: str = "en",
        minor_multiplier: int = 100,
        include_symbol: bool = True,
        use_native_digits: bool = False
    ) -> str:
        """
        Formats integer minor units into a localized currency string.
        Supports 2-decimal (BDT, USD, CNY, EUR, SAR), 3-decimal (KWD, OMR), and 0-decimal (JPY) currencies.
        """
        # Determine decimal places from multiplier
        if minor_multiplier == 1000:
            decimal_places = 3
        elif minor_multiplier == 1:
            decimal_places = 0
        else:
            decimal_places = 2

        major_decimal = Decimal(amount_minor) / Decimal(minor_multiplier)
        formatted_num = cls.format_number(
            major_decimal,
            locale=locale,
            decimal_places=decimal_places,
            use_native_digits=use_native_digits
        )

        currency_symbols = {
            "BDT": "৳",
            "CNY": "¥",
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "SAR": "﷼",
            "KWD": "KD",
            "AED": "د.إ",
            "INR": "₹",
            "PKR": "₨",
            "JPY": "¥",
            "AUD": "A$",
            "CAD": "C$",
            "UZS": "so'm",
        }

        sym = currency_symbols.get(currency.upper(), currency.upper())

        # Check script direction
        entry = LanguageRegistry.get(locale)
        is_rtl = entry and entry.direction == TextDirection.RTL

        if not include_symbol:
            return formatted_num

        if is_rtl:
            return f"{formatted_num} {sym}"
        return f"{sym} {formatted_num}"

    @classmethod
    def format_chinese_financial_units(cls, amount_minor: int, minor_multiplier: int = 100) -> str:
        """
        Formats large monetary values using standard Chinese SME commercial units:
        Wan (万 - 10,000) and Yi (亿 - 100,000,000).
        Example: 500,000 CNY -> '¥ 50.00万元', 12,850,000 CNY -> '¥ 1,285.00万元'.
        """
        major = Decimal(amount_minor) / Decimal(minor_multiplier)
        if abs(major) >= Decimal("100000000"):
            yi = major / Decimal("100000000")
            return f"¥ {yi:,.2f}亿元"
        elif abs(major) >= Decimal("10000"):
            wan = major / Decimal("10000")
            return f"¥ {wan:,.2f}万元"
        else:
            return f"¥ {major:,.2f}元"

    @classmethod
    def parse_localized_number(cls, text: str, locale: str = "en") -> Optional[Decimal]:
        """
        Safely parses a localized number string into an exact Decimal.
        Handles both dot-decimal ('1,250.50') and comma-decimal ('1.250,50') formats.
        """
        if not text:
            return None

        # 1. Normalize native digits to ASCII 0-9
        normalized = cls.normalize_digits_to_ascii(text.strip())

        # 2. Detect decimal format
        # If both '.' and ',' appear, the last one is the decimal separator
        has_comma = "," in normalized
        has_dot = "." in normalized

        if has_comma and has_dot:
            last_comma = normalized.rfind(",")
            last_dot = normalized.rfind(".")
            if last_comma > last_dot:
                # Comma is decimal separator: e.g. 1.250,50
                clean = normalized.replace(".", "").replace(" ", "").replace(",", ".")
            else:
                # Dot is decimal separator: e.g. 1,250.50
                clean = normalized.replace(",", "").replace(" ", "")
        elif has_comma:
            # Check if it looks like decimal or thousands separator
            parts = normalized.split(",")
            if len(parts) == 2 and len(parts[1]) in (1, 2, 3):
                # Likely decimal: 1250,50
                clean = normalized.replace(" ", "").replace(",", ".")
            else:
                # Likely thousands: 1,250
                clean = normalized.replace(",", "").replace(" ", "")
        else:
            clean = normalized.replace(" ", "")

        # Remove any remaining non-digit non-dot non-minus characters
        clean = re.sub(r"[^\d.-]", "", clean)
        if not clean or clean == "-" or clean == ".":
            return None

        try:
            return Decimal(clean)
        except Exception:
            return None

    @classmethod
    def get_text_direction(cls, locale: str) -> str:
        """Returns 'rtl' or 'ltr'."""
        entry = LanguageRegistry.get(locale)
        if entry:
            return entry.direction.value
        return "ltr"
