"""Unit tests for Multi-Country Profiles and Financial Regulatory Rules."""

import pytest
from src.core.country_profiles import (
    CountryRegistry,
    CountryProfile,
    VerificationStatus,
)
from src.core.money import Money


class TestCountryProfiles:
    """Verify country financial regulations, statutory tax rates, and official legal citations."""

    def test_all_seven_candidate_jurisdictions_loaded(self):
        profiles = CountryRegistry.get_all()
        assert len(profiles) >= 7
        expected_countries = {"BD", "CN", "SA", "US", "AU", "KW", "UZ"}
        loaded_codes = {p.country_code for p in profiles}
        for code in expected_countries:
            assert code in loaded_codes, f"Expected jurisdiction {code} not in loaded profiles"

    def test_profile_schema_completeness(self):
        required_fields = [
            "country_code",
            "country_name",
            "primary_currency",
            "currency_symbol",
            "minor_unit_multiplier",
            "tax_authority_name",
            "standard_vat_rate_pct",
            "corporate_income_tax_rate_pct",
            "accounting_standard",
            "statutory_dscr_covenant",
            "invoice_standard_name",
            "sources",
        ]
        for p in CountryRegistry.get_all():
            d = p.to_dict()
            for field in required_fields:
                assert field in d, f"Country {p.country_code} missing required field {field}"
            assert len(p.sources) > 0, f"Country {p.country_code} has no verified sources"

    def test_china_profile_accuracy(self):
        cn = CountryRegistry.get("CN")
        assert cn is not None
        assert cn.primary_currency == "CNY"
        assert "State Taxation Administration" in cn.tax_authority_name
        assert cn.standard_vat_rate_pct == 13.0
        assert 9.0 in cn.reduced_vat_rates_pct
        assert 6.0 in cn.reduced_vat_rates_pct
        assert cn.corporate_income_tax_rate_pct == 25.0  # Headline statutory CIT rate (preferential SME 5% detailed in sources)
        assert "全电发票" in cn.invoice_standard_name or "Fapiao" in cn.invoice_standard_name
        # Check source citations
        source_texts = " ".join(s.regulatory_source for s in cn.sources)
        assert "SAT" in source_texts or "State Taxation Administration" in source_texts

    def test_bangladesh_profile_accuracy(self):
        bd = CountryRegistry.get("BD")
        assert bd is not None
        assert bd.primary_currency == "BDT"
        assert "National Board of Revenue" in bd.tax_authority_name
        assert bd.standard_vat_rate_pct == 15.0
        assert bd.statutory_dscr_covenant == 1.25
        source_texts = " ".join(s.regulatory_source for s in bd.sources)
        assert "2012" in source_texts  # VAT Act 2012

    def test_kuwait_3_decimal_precision(self):
        kw = CountryRegistry.get("KW")
        assert kw is not None
        assert kw.primary_currency == "KWD"
        assert kw.minor_unit_multiplier == 1000
        assert kw.statutory_dscr_covenant == 1.25

        # Money class precision verification with 3 minor decimals
        m = Money.from_minor(1250500, "KWD")
        assert m.amount_minor == 1250500
        assert m.amount_major == 1250.5
        assert m.format() == "1,250.500 KWD"

    def test_saudi_arabia_zatca_compliance(self):
        sa = CountryRegistry.get("SA")
        assert sa is not None
        assert sa.primary_currency == "SAR"
        assert "ZATCA" in sa.tax_authority_name or "Zakat" in sa.tax_authority_name
        assert sa.standard_vat_rate_pct == 15.0
        source_texts = " ".join(s.regulatory_source for s in sa.sources)
        assert "ZATCA" in source_texts

    def test_multiplier_lookup(self):
        assert CountryRegistry.get_currency_multiplier("KWD") == 1000
        assert CountryRegistry.get_currency_multiplier("BDT") == 100
        assert CountryRegistry.get_currency_multiplier("CNY") == 100
        assert CountryRegistry.get_currency_multiplier("USD") == 100
        assert CountryRegistry.get_currency_multiplier("UNKNOWN") == 100
