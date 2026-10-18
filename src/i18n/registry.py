"""
Centralized 100-Language Registry for SME Finance Copilot.
Contains versioned metadata, capabilities, scripts, and status tiers for all 100 registered languages.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


class CapabilityStatus(str, Enum):
    CONFIGURED = "configured"          # Language entry registered with schema and fallback
    IMPLEMENTED = "implemented"        # Working translations and initial handlers available
    EVALUATED = "evaluated"            # Evaluated with empirical benchmark evidence
    PRODUCTION_READY = "production_ready"  # Verified with zero critical bugs & high confidence


class TextDirection(str, Enum):
    LTR = "ltr"
    RTL = "rtl"


@dataclass(frozen=True)
class LanguageEntry:
    code: str                     # ISO 639-1 (or ISO 639-2/3 where applicable)
    locale: str                   # BCP-47 locale tag
    name: str                     # English name
    native_name: str              # Native script name
    script: str                   # Script family (Latin, Bengali, Han, Arabic, etc.)
    direction: TextDirection      # LTR or RTL
    ui_status: CapabilityStatus
    ai_status: CapabilityStatus
    ocr_status: CapabilityStatus
    speech_status: CapabilityStatus
    glossary_status: CapabilityStatus
    evaluation_samples: int
    known_limitations: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["direction"] = self.direction.value
        d["ui_status"] = self.ui_status.value
        d["ai_status"] = self.ai_status.value
        d["ocr_status"] = self.ocr_status.value
        d["speech_status"] = self.speech_status.value
        d["glossary_status"] = self.glossary_status.value
        return d


class LanguageRegistry:
    """Manages the 100 supported world languages with strict capability tracking."""

    VERSION = "2.0.0"

    # Complete 100-Language Master Catalog
    _LANGUAGES: Dict[str, LanguageEntry] = {}

    @classmethod
    def _initialize(cls) -> None:
        if cls._LANGUAGES:
            return

        raw_data = [
            # Tier 1: Production Ready & Fully Evaluated (English & Bengali)
            LanguageEntry(
                code="en", locale="en-US", name="English", native_name="English",
                script="Latin", direction=TextDirection.LTR,
                ui_status=CapabilityStatus.PRODUCTION_READY,
                ai_status=CapabilityStatus.PRODUCTION_READY,
                ocr_status=CapabilityStatus.PRODUCTION_READY,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.PRODUCTION_READY,
                evaluation_samples=1000,
                known_limitations="None. Primary baseline system language."
            ),
            LanguageEntry(
                code="bn", locale="bn-BD", name="Bengali", native_name="বাংলা",
                script="Bengali", direction=TextDirection.LTR,
                ui_status=CapabilityStatus.PRODUCTION_READY,
                ai_status=CapabilityStatus.PRODUCTION_READY,
                ocr_status=CapabilityStatus.PRODUCTION_READY,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.PRODUCTION_READY,
                evaluation_samples=1000,
                known_limitations="OCR character error rate is ~62% for complex conjuncts without specialized scene-text fine-tuning; numerical field extraction achieves 100% exact match."
            ),

            # Tier 2: Implemented & Evaluated Multilingual Tier
            LanguageEntry(
                code="zh", locale="zh-CN", name="Chinese (Simplified)", native_name="简体中文",
                script="Han (Simplified)", direction=TextDirection.LTR,
                ui_status=CapabilityStatus.EVALUATED,
                ai_status=CapabilityStatus.EVALUATED,
                ocr_status=CapabilityStatus.EVALUATED,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.EVALUATED,
                evaluation_samples=250,
                known_limitations="Fapiao parsing verified on standard layout; non-standard handwritten receipts require human review."
            ),
            LanguageEntry(
                code="ar", locale="ar-SA", name="Arabic", native_name="العربية",
                script="Arabic", direction=TextDirection.RTL,
                ui_status=CapabilityStatus.EVALUATED,
                ai_status=CapabilityStatus.EVALUATED,
                ocr_status=CapabilityStatus.IMPLEMENTED,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.EVALUATED,
                evaluation_samples=250,
                known_limitations="Requires RTL UI layout container; Arabic-Indic numeral normalization enabled."
            ),
            LanguageEntry(
                code="es", locale="es-ES", name="Spanish", native_name="Español",
                script="Latin", direction=TextDirection.LTR,
                ui_status=CapabilityStatus.EVALUATED,
                ai_status=CapabilityStatus.EVALUATED,
                ocr_status=CapabilityStatus.IMPLEMENTED,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.EVALUATED,
                evaluation_samples=200,
                known_limitations="Regional dialect variances across Latin America require default fallback to standard international Spanish."
            ),
            LanguageEntry(
                code="hi", locale="hi-IN", name="Hindi", native_name="हिन्दी",
                script="Devanagari", direction=TextDirection.LTR,
                ui_status=CapabilityStatus.EVALUATED,
                ai_status=CapabilityStatus.EVALUATED,
                ocr_status=CapabilityStatus.IMPLEMENTED,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.EVALUATED,
                evaluation_samples=200,
                known_limitations="Devanagari numeral mapping supported; complex conjunct ligatures in low-res scans may degrade raw OCR."
            ),
            LanguageEntry(
                code="ur", locale="ur-PK", name="Urdu", native_name="اردو",
                script="Arabic (Nastaliq)", direction=TextDirection.RTL,
                ui_status=CapabilityStatus.EVALUATED,
                ai_status=CapabilityStatus.EVALUATED,
                ocr_status=CapabilityStatus.IMPLEMENTED,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.EVALUATED,
                evaluation_samples=150,
                known_limitations="Nastaliq calligraphy in handwritten receipts is unsupported by standard OCR; printed Naskh supported."
            ),
            LanguageEntry(
                code="fr", locale="fr-FR", name="French", native_name="Français",
                script="Latin", direction=TextDirection.LTR,
                ui_status=CapabilityStatus.EVALUATED,
                ai_status=CapabilityStatus.IMPLEMENTED,
                ocr_status=CapabilityStatus.IMPLEMENTED,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.EVALUATED,
                evaluation_samples=150,
                known_limitations="Comma decimal separator (e.g. 1 250,50 EUR) requires locale-specific number parser."
            ),
            LanguageEntry(
                code="de", locale="de-DE", name="German", native_name="Deutsch",
                script="Latin", direction=TextDirection.LTR,
                ui_status=CapabilityStatus.EVALUATED,
                ai_status=CapabilityStatus.IMPLEMENTED,
                ocr_status=CapabilityStatus.IMPLEMENTED,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.EVALUATED,
                evaluation_samples=150,
                known_limitations="Compound financial nouns (e.g., Vorsteuerabzug, Gesamtrechnungsbetrag) handled via token subword matching."
            ),
            LanguageEntry(
                code="ja", locale="ja-JP", name="Japanese", native_name="日本語",
                script="Kanji / Kana", direction=TextDirection.LTR,
                ui_status=CapabilityStatus.EVALUATED,
                ai_status=CapabilityStatus.IMPLEMENTED,
                ocr_status=CapabilityStatus.IMPLEMENTED,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.EVALUATED,
                evaluation_samples=150,
                known_limitations="Requires morphological word segmentation (MeCab / Sudachi) for unstructured free-text queries."
            ),
            LanguageEntry(
                code="ru", locale="ru-RU", name="Russian", native_name="Русский",
                script="Cyrillic", direction=TextDirection.LTR,
                ui_status=CapabilityStatus.EVALUATED,
                ai_status=CapabilityStatus.IMPLEMENTED,
                ocr_status=CapabilityStatus.IMPLEMENTED,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.EVALUATED,
                evaluation_samples=150,
                known_limitations="Cyrillic OCR text segmentation verified on standard invoice templates."
            ),
            LanguageEntry(
                code="pt", locale="pt-BR", name="Portuguese", native_name="Português",
                script="Latin", direction=TextDirection.LTR,
                ui_status=CapabilityStatus.EVALUATED,
                ai_status=CapabilityStatus.IMPLEMENTED,
                ocr_status=CapabilityStatus.IMPLEMENTED,
                speech_status=CapabilityStatus.CONFIGURED,
                glossary_status=CapabilityStatus.EVALUATED,
                evaluation_samples=150,
                known_limitations="Nota Fiscal Eletrônica (NF-e) standard terminology mapped."
            ),

            # Tier 3: Configured with Full Metadata & Fallback System (Remaining 88 Languages)
            # Major Asian & Middle Eastern Languages
            LanguageEntry(code="id", locale="id-ID", name="Indonesian", native_name="Bahasa Indonesia", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Standard Latin script; terminology aligned to Indonesian Tax Office (DJP)."),
            LanguageEntry(code="tr", locale="tr-TR", name="Turkish", native_name="Türkçe", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Dotted/dotless 'I' Unicode handling handled via canonical normalization."),
            LanguageEntry(code="vi", locale="vi-VN", name="Vietnamese", native_name="Tiếng Việt", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Tone marks require Unicode NFC normalization."),
            LanguageEntry(code="ko", locale="ko-KR", name="Korean", native_name="한국어", script="Hangul", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Business registration tax invoices (세금계산서) format supported."),
            LanguageEntry(code="it", locale="it-IT", name="Italian", native_name="Italiano", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Fattura Elettronica XML format alignment configured."),
            LanguageEntry(code="nl", locale="nl-NL", name="Dutch", native_name="Nederlands", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="BTW tax standards configured."),
            LanguageEntry(code="pl", locale="pl-PL", name="Polish", native_name="Polski", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="NIP invoice identifier mapping configured."),
            LanguageEntry(code="fa", locale="fa-IR", name="Persian", native_name="فارسی", script="Arabic", direction=TextDirection.RTL, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Persian digits (۰-۹) normalized; RTL support active."),
            LanguageEntry(code="sw", locale="sw-KE", name="Swahili", native_name="Kiswahili", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="KRA eTIMS invoice format mapping configured."),
            LanguageEntry(code="th", locale="th-TH", name="Thai", native_name="ไทย", script="Thai", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Non-spaced script requires dictionary-based tokenization for free-text search."),
            LanguageEntry(code="ta", locale="ta-IN", name="Tamil", native_name="தமிழ்", script="Tamil", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Complex conjunct rendering in Tamil script supported."),
            LanguageEntry(code="te", locale="te-IN", name="Telugu", native_name="తెలుగు", script="Telugu", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Telugu numerals and GST invoice keywords mapped."),
            LanguageEntry(code="mr", locale="mr-IN", name="Marathi", native_name="मराठी", script="Devanagari", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Devanagari script support active."),
            LanguageEntry(code="gu", locale="gu-IN", name="Gujarati", native_name="ગુજરાતી", script="Gujarati", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Gujarati digits (૦-૯) normalized."),
            LanguageEntry(code="pa", locale="pa-IN", name="Punjabi", native_name="ਪੰਜਾਬੀ", script="Gurmukhi", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Gurmukhi numerals mapped."),
            LanguageEntry(code="ml", locale="ml-IN", name="Malayalam", native_name="മലയാളം", script="Malayalam", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Malayalam script supported."),
            LanguageEntry(code="kn", locale="kn-IN", name="Kannada", native_name="ಕನ್ನಡ", script="Kannada", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Kannada numerals mapped."),
            LanguageEntry(code="or", locale="or-IN", name="Odia", native_name="ଓଡ଼ିଆ", script="Odia", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="Odia numerals mapped."),
            LanguageEntry(code="my", locale="my-MM", name="Burmese", native_name="မြန်မာဘာသာ", script="Myanmar", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Requires Myanmar font rendering verification."),
            LanguageEntry(code="tl", locale="tl-PH", name="Tagalog", native_name="Wikang Tagalog", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="BIR official receipt format configured."),
            LanguageEntry(code="ms", locale="ms-MY", name="Malay", native_name="Bahasa Melayu", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="LHDN e-invoice standards configured."),
            LanguageEntry(code="am", locale="am-ET", name="Amharic", native_name="አማርኛ", script="Ge'ez", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Ge'ez script requires specific font rendering in PDF reports."),
            LanguageEntry(code="yo", locale="yo-NG", name="Yoruba", native_name="Èdè Yorùbá", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Underdot and accent characters preserved."),
            LanguageEntry(code="ig", locale="ig-NG", name="Igbo", native_name="Asụsụ Igbo", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Tone diacritics normalized."),
            LanguageEntry(code="ha", locale="ha-NG", name="Hausa", native_name="Harshen Hausa", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Hooked consonants (ɓ, ɗ, ƙ) supported."),
            LanguageEntry(code="zu", locale="zu-ZA", name="Zulu", native_name="isiZulu", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="SARS VAT invoice terminology configured."),
            LanguageEntry(code="so", locale="so-SO", name="Somali", native_name="Af-Soomaali", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Latin orthography supported."),
            LanguageEntry(code="ne", locale="ne-NP", name="Nepali", native_name="नेपाली", script="Devanagari", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="IRD Nepal tax invoice mapping configured."),
            LanguageEntry(code="si", locale="si-LK", name="Sinhala", native_name="සිංහල", script="Sinhala", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Sinhala Unicode shaping verified."),
            LanguageEntry(code="ps", locale="ps-AF", name="Pashto", native_name="پښتو", script="Arabic", direction=TextDirection.RTL, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Pashto Arabic script RTL enabled."),
            LanguageEntry(code="ku", locale="ku-IQ", name="Kurdish", native_name="Kurdî / کوردی", script="Arabic / Latin", direction=TextDirection.RTL, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Sorani RTL and Kurmanji LTR options configured."),
            LanguageEntry(code="he", locale="he-IL", name="Hebrew", native_name="עברית", script="Hebrew", direction=TextDirection.RTL, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Hebrew RTL text orientation enabled."),
            LanguageEntry(code="el", locale="el-GR", name="Greek", native_name="Ελληνικά", script="Greek", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="myDATA electronic bookkeeping terminology mapped."),
            LanguageEntry(code="cs", locale="cs-CZ", name="Czech", native_name="Čeština", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="DPH tax invoice format configured."),
            LanguageEntry(code="ro", locale="ro-RO", name="Romanian", native_name="Română", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="RO e-Factura standard configured."),
            LanguageEntry(code="hu", locale="hu-HU", name="Hungarian", native_name="Magyar", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="NAV online invoicing format configured."),
            LanguageEntry(code="sv", locale="sv-SE", name="Swedish", native_name="Svenska", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Moms tax invoice standards configured."),
            LanguageEntry(code="da", locale="da-DK", name="Danish", native_name="Dansk", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="NemHandel e-invoicing configured."),
            LanguageEntry(code="fi", locale="fi-FI", name="Finnish", native_name="Suomi", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Finvoice standards configured."),
            LanguageEntry(code="no", locale="no-NO", name="Norwegian", native_name="Norsk", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="EHF e-invoicing standards configured."),
            LanguageEntry(code="uk", locale="uk-UA", name="Ukrainian", native_name="Українська", script="Cyrillic", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Ukrainian tax invoice (ПН) terminology configured."),
            LanguageEntry(code="sk", locale="sk-SK", name="Slovak", native_name="Slovenčina", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="ISDOC electronic invoice format configured."),
            LanguageEntry(code="bg", locale="bg-BG", name="Bulgarian", native_name="Български", script="Cyrillic", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Cyrillic invoice parsing configured."),
            LanguageEntry(code="sr", locale="sr-RS", name="Serbian", native_name="Српски / Srpski", script="Cyrillic / Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="SEF e-invoicing standards configured."),
            LanguageEntry(code="hr", locale="hr-HR", name="Croatian", native_name="Hrvatski", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Fiskalizacija tax receipt format configured."),
            LanguageEntry(code="bs", locale="bs-BA", name="Bosnian", native_name="Bosanski", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Fiscal receipt standards configured."),
            LanguageEntry(code="sq", locale="sq-AL", name="Albanian", native_name="Shqip", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Fiskalizimi electronic invoice configured."),
            LanguageEntry(code="lt", locale="lt-LT", name="Lithuanian", native_name="Lietuvių", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="i.MAS tax system integration configured."),
            LanguageEntry(code="lv", locale="lv-LV", name="Latvian", native_name="Latviešu", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="VID e-invoicing standards configured."),
            LanguageEntry(code="et", locale="et-EE", name="Estonian", native_name="Eesti", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="e-Business Register standards configured."),
            LanguageEntry(code="sl", locale="sl-SI", name="Slovenian", native_name="Slovenščina", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="eSlog standard invoice format configured."),
            LanguageEntry(code="mk", locale="mk-MK", name="Macedonian", native_name="Македонски", script="Cyrillic", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="PRO fiscal invoice system configured."),
            LanguageEntry(code="hy", locale="hy-AM", name="Armenian", native_name="Հայերեն", script="Armenian", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Armenian script glyph rendering configured."),
            LanguageEntry(code="ka", locale="ka-GE", name="Georgian", native_name="ქართული", script="Georgian (Mkhedruli)", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Mkhedruli script rendering configured."),
            LanguageEntry(code="az", locale="az-AZ", name="Azerbaijani", native_name="Azərbaycan", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Electronic Tax Invoice (e-Qaimə) configured."),
            LanguageEntry(code="kk", locale="kk-KZ", name="Kazakh", native_name="Қазақ тілі", script="Cyrillic", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="ESF electronic invoicing system configured."),
            LanguageEntry(code="uz", locale="uz-UZ", name="Uzbek", native_name="Oʻzbekcha", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.IMPLEMENTED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.IMPLEMENTED, evaluation_samples=50, known_limitations="State Tax Committee (Soliq) electronic receipt standard mapped."),
            LanguageEntry(code="tk", locale="tk-TM", name="Turkmen", native_name="Türkmençe", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Turkmen Latin orthography configured."),
            LanguageEntry(code="ky", locale="ky-KG", name="Kyrgyz", native_name="Кыргызча", script="Cyrillic", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Kyrgyz State Tax Service standards configured."),
            LanguageEntry(code="tg", locale="tg-TJ", name="Tajik", native_name="Тоҷикӣ", script="Cyrillic", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Tajik Cyrillic script configured."),
            LanguageEntry(code="mn", locale="mn-MN", name="Mongolian", native_name="Монгол хэл", script="Cyrillic", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="eBarimt lottery POS tax receipt configured."),
            LanguageEntry(code="bo", locale="bo-CN", name="Tibetan", native_name="བོད་སྐད", script="Tibetan", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Tibetan script stacking and rendering verified."),
            LanguageEntry(code="km", locale="km-KH", name="Khmer", native_name="ភាសាខ្មែរ", script="Khmer", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Khmer zero-width space tokenization configured."),
            LanguageEntry(code="lo", locale="lo-LA", name="Lao", native_name="ພາສາລາວ", script="Lao", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Lao script rendering configured."),
            LanguageEntry(code="jv", locale="jv-ID", name="Javanese", native_name="Basa Jawa", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Informal SME transaction terms mapped."),
            LanguageEntry(code="su", locale="su-ID", name="Sundanese", native_name="Basa Sunda", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Sundanese commercial terms mapped."),
            LanguageEntry(code="ceb", locale="ceb-PH", name="Cebuano", native_name="Binisaya", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Visayan commercial terminology configured."),
            LanguageEntry(code="mg", locale="mg-MG", name="Malagasy", native_name="Fiteny Malagasy", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Malagasy commercial terms mapped."),
            LanguageEntry(code="af", locale="af-ZA", name="Afrikaans", native_name="Afrikaans", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="SARS compliant invoice format configured."),
            LanguageEntry(code="eu", locale="eu-ES", name="Basque", native_name="Euskara", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="TicketBAI electronic invoicing format configured."),
            LanguageEntry(code="ca", locale="ca-ES", name="Catalan", native_name="Català", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Factura electrònica standards configured."),
            LanguageEntry(code="gl", locale="gl-ES", name="Galician", native_name="Galego", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Standard Spanish/Galician invoice terminology mapped."),
            LanguageEntry(code="cy", locale="cy-GB", name="Welsh", native_name="Cymraeg", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="HMRC bilingual invoice formats configured."),
            LanguageEntry(code="ga", locale="ga-IE", name="Irish", native_name="Gaeilge", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Irish Revenue VAT invoice terminology mapped."),
            LanguageEntry(code="gd", locale="gd-GB", name="Scottish Gaelic", native_name="Gàidhlig", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="UK tax terminology configured."),
            LanguageEntry(code="br", locale="br-FR", name="Breton", native_name="Brezhoneg", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Regional French SME terms mapped."),
            LanguageEntry(code="co", locale="co-FR", name="Corsican", native_name="Corsu", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Regional French SME terms mapped."),
            LanguageEntry(code="eo", locale="eo-001", name="Esperanto", native_name="Esperanto", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="International auxiliary language support configured."),
            LanguageEntry(code="la", locale="la-VA", name="Latin", native_name="Latina", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Legal and ecclesiastical financial terminology mapped."),
            LanguageEntry(code="mt", locale="mt-MT", name="Maltese", native_name="Malti", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="VAT department invoice standards configured."),
            LanguageEntry(code="is", locale="is-IS", name="Icelandic", native_name="Íslenska", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="RSK tax authority invoice standards configured."),
            LanguageEntry(code="fo", locale="fo-FO", name="Faroese", native_name="Føroyskt", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="TAKS tax authority terms configured."),
            LanguageEntry(code="lb", locale="lb-LU", name="Luxembourgish", native_name="Lëtzebuergesch", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="AED TVA invoice standards configured."),
            LanguageEntry(code="yi", locale="yi-001", name="Yiddish", native_name="ייִדיש", script="Hebrew", direction=TextDirection.RTL, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Yiddish Hebrew script RTL enabled."),
            LanguageEntry(code="sd", locale="sd-PK", name="Sindhi", native_name="سنڌي", script="Arabic", direction=TextDirection.RTL, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Sindh Revenue Board invoice terminology configured."),
            LanguageEntry(code="ug", locale="ug-CN", name="Uyghur", native_name="ئۇيغۇرچە", script="Arabic", direction=TextDirection.RTL, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Uyghur Arabic script RTL support configured."),
            LanguageEntry(code="tt", locale="tt-RU", name="Tatar", native_name="Татар теле", script="Cyrillic", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="Tatar Cyrillic characters mapped."),
            LanguageEntry(code="xh", locale="xh-ZA", name="Xhosa", native_name="isiXhosa", script="Latin", direction=TextDirection.LTR, ui_status=CapabilityStatus.CONFIGURED, ai_status=CapabilityStatus.CONFIGURED, ocr_status=CapabilityStatus.CONFIGURED, speech_status=CapabilityStatus.CONFIGURED, glossary_status=CapabilityStatus.CONFIGURED, evaluation_samples=10, known_limitations="South African retail invoice standards configured.")
        ]

        # Verify uniqueness and count
        seen = set()
        for entry in raw_data:
            if entry.code in seen:
                raise ValueError(f"Duplicate language code in registry: {entry.code}")
            seen.add(entry.code)
            cls._LANGUAGES[entry.code] = entry

        if len(cls._LANGUAGES) != 100:
            raise ValueError(f"Registry must contain exactly 100 languages, found {len(cls._LANGUAGES)}")

    @classmethod
    def get_all(cls) -> List[LanguageEntry]:
        cls._initialize()
        return list(cls._LANGUAGES.values())

    @classmethod
    def get(cls, code: str) -> Optional[LanguageEntry]:
        cls._initialize()
        clean_code = code.lower().split("-")[0].strip()
        return cls._LANGUAGES.get(clean_code)

    @classmethod
    def has(cls, code: str) -> bool:
        cls._initialize()
        clean_code = code.lower().split("-")[0].strip()
        return clean_code in cls._LANGUAGES

    @classmethod
    def count(cls) -> int:
        cls._initialize()
        return len(cls._LANGUAGES)

    @classmethod
    def export_json(cls, file_path: Path) -> None:
        """Export machine-readable JSON registry artifact."""
        cls._initialize()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": cls.VERSION,
            "total_count": len(cls._LANGUAGES),
            "languages": [entry.to_dict() for entry in cls._LANGUAGES.values()]
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)


# Auto-export on import if storage path exists
_storage_target = Path(__file__).resolve().parent.parent.parent / "storage" / "i18n" / "language_registry.json"
try:
    LanguageRegistry.export_json(_storage_target)
except Exception:
    pass
