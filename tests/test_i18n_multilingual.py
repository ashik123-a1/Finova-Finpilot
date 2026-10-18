"""Unit tests for Centralized i18n System and 100-Language Registry."""

import pytest
from src.i18n.registry import (
    LanguageRegistry,
    LanguageEntry,
    CapabilityStatus,
    TextDirection,
)
from src.i18n.translator import I18nService, t
from src.i18n.formatters import LocaleFormatter


class TestLanguageRegistry:
    """Verify 100-language registry integrity and capability tiers."""

    def test_registry_contains_100_languages(self):
        languages = LanguageRegistry.get_all()
        assert len(languages) == 100, f"Expected exactly 100 languages, found {len(languages)}"
        assert LanguageRegistry.count() == 100

    def test_language_schema_completeness(self):
        for lang in LanguageRegistry.get_all():
            d = lang.to_dict()
            required_keys = [
                "code", "locale", "name", "native_name", "script",
                "direction", "ui_status", "ai_status", "ocr_status",
                "speech_status", "glossary_status", "evaluation_samples", "known_limitations"
            ]
            for k in required_keys:
                assert k in d, f"Language {lang.code} missing dict key {k}"

            assert lang.direction in [TextDirection.LTR, TextDirection.RTL]
            assert isinstance(lang.ui_status, CapabilityStatus)
            assert isinstance(lang.ai_status, CapabilityStatus)

    def test_rtl_languages_detected(self):
        rtl_langs = [l for l in LanguageRegistry.get_all() if l.direction == TextDirection.RTL]
        rtl_codes = {l.code for l in rtl_langs}
        expected_rtl = {"ar", "ur", "fa", "ps", "ku", "he", "yi", "sd", "ug"}
        for code in expected_rtl:
            assert code in rtl_codes, f"Expected RTL language {code} not flagged as RTL"

    def test_language_lookup(self):
        zh = LanguageRegistry.get("zh")
        assert zh is not None
        assert "Chinese" in zh.name
        assert zh.direction == TextDirection.LTR

        ar = LanguageRegistry.get("ar")
        assert ar is not None
        assert ar.direction == TextDirection.RTL

        invalid = LanguageRegistry.get("nonexistent_xx")
        assert invalid is None


class TestTranslationEngine:
    """Verify I18nService catalog integrity, fallback, and financial fact preservation."""

    def test_catalogs_loaded(self):
        service = I18nService()
        locales = service.get_loaded_locales()
        for loc in ["en", "bn", "zh", "ar", "es", "hi"]:
            assert loc in locales, f"Expected locale {loc} to be loaded"

    def test_master_catalog_validation(self):
        service = I18nService()
        validation = service.validate_catalogs()
        assert validation["master_key_count"] > 50
        for loc, status in validation["results"].items():
            assert status["missing_keys_count"] == 0, f"Locale {loc} has missing keys"
            assert len(status["placeholder_mismatches"]) == 0, f"Locale {loc} has placeholder discrepancies"

    def test_translation_fallback_to_english(self):
        service = I18nService()
        # Fallback to English for nonexistent locale
        result_fallback = service.translate("common.save", locale="xx")
        assert result_fallback == "Save"

        # Direct English translation
        assert service.translate("common.save", locale="en") == "Save"
        assert service.translate("common.save", locale="zh") == "保存"
        assert service.translate("common.save", locale="bn") == "সংরক্ষণ করুন"

    def test_financial_fact_preservation(self):
        """Financial facts (amounts, signs, decimals, IDs) must NOT be distorted across translations."""
        service = I18nService()
        tokens = {
            "amount": "12,450.50",
            "currency": "BDT",
            "invoice_id": "INV-2026-9901",
        }

        en_text = service.translate("documents.extracted_total", locale="en", **tokens)
        zh_text = service.translate("documents.extracted_total", locale="zh", **tokens)
        ar_text = service.translate("documents.extracted_total", locale="ar", **tokens)
        bn_text = service.translate("documents.extracted_total", locale="bn", **tokens)

        # All versions must retain the exact numerical value and currency code
        for text in [en_text, zh_text, ar_text, bn_text]:
            assert "12,450.50" in text
            assert "BDT" in text

    def test_helper_function_t(self):
        assert t("common.cancel", "en") == "Cancel"
        assert t("common.cancel", "zh") == "取消"
        assert t("common.cancel", "ar") == "إلغاء"


class TestLocaleFormatter:
    """Verify number, currency, digit conversion, and RTL helpers."""

    def test_currency_formatting_decimals(self):
        # 2-decimal standard
        assert LocaleFormatter.format_currency(123456, "USD") == "$ 1,234.56"
        assert LocaleFormatter.format_currency(123456, "BDT") == "৳ 1,234.56"
        assert LocaleFormatter.format_currency(123456, "CNY") == "¥ 1,234.56"

        # 3-decimal KWD
        assert LocaleFormatter.format_currency(1234567, "KWD", minor_multiplier=1000) == "KD 1,234.567"

        # 0-decimal JPY
        assert LocaleFormatter.format_currency(123456, "JPY", minor_multiplier=1) == "¥ 123,456"

    def test_digit_conversion(self):
        ascii_digits = "1234567890"

        # Bengali
        bn_digits = LocaleFormatter.convert_digits_to_native(ascii_digits, "bn")
        assert bn_digits == "১২৩৪৫৬৭৮৯০"
        assert LocaleFormatter.convert_native_to_ascii(bn_digits) == ascii_digits

        # Arabic-Indic
        ar_digits = LocaleFormatter.convert_digits_to_native(ascii_digits, "ar")
        assert ar_digits == "١٢٣٤٥٦٧٨٩٠"
        assert LocaleFormatter.convert_native_to_ascii(ar_digits) == ascii_digits

        # Devanagari
        hi_digits = LocaleFormatter.convert_digits_to_native(ascii_digits, "hi")
        assert hi_digits == "१२३४५६७८९०"
        assert LocaleFormatter.convert_native_to_ascii(hi_digits) == ascii_digits

    def test_rtl_detection(self):
        assert LocaleFormatter.get_text_direction("ar") == "rtl"
        assert LocaleFormatter.get_text_direction("fa") == "rtl"
        assert LocaleFormatter.get_text_direction("ur") == "rtl"
        assert LocaleFormatter.get_text_direction("en") == "ltr"
        assert LocaleFormatter.get_text_direction("zh") == "ltr"
