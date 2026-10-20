"""
Centralized Translation and Internationalization (i18n) Engine.
Protects financial entities during translation, supports graceful fallback,
and validates placeholder integrity across languages.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from src.i18n.registry import LanguageRegistry


@dataclass(frozen=True)
class TranslationResult:
    text: str
    is_fallback: bool
    requested_locale: str
    resolved_locale: str
    key: str


class I18nService:
    """Manages multi-language string lookup, token interpolation, and fallback resolution."""

    DEFAULT_LOCALE = "en"
    _LOCALES_DIR = Path(__file__).resolve().parent / "locales"
    _CATALOGS: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _load_catalogs(cls, force: bool = False) -> None:
        if cls._CATALOGS and not force:
            return

        cls._CATALOGS = {}
        for f in cls._LOCALES_DIR.glob("*.json"):
            lang_code = f.stem.lower()
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    cls._CATALOGS[lang_code] = json.load(fp)
            except Exception:
                pass

        # Guarantee English default is loaded
        if cls.DEFAULT_LOCALE not in cls._CATALOGS:
            cls._CATALOGS[cls.DEFAULT_LOCALE] = {}

    @classmethod
    def reload_catalogs(cls) -> None:
        """Force reloads all JSON translation files from disk."""
        cls._load_catalogs(force=True)

    @classmethod
    def get_loaded_locales(cls) -> List[str]:
        cls._load_catalogs()
        return list(cls._CATALOGS.keys())

    @classmethod
    def translate(cls, key: str, locale: str = "en", **kwargs: Any) -> str:
        """Convenience method returning translated string directly."""
        return cls.get_translation(key, locale=locale, **kwargs).text

    @classmethod
    def validate_catalogs(cls) -> Dict[str, Any]:
        """Alias for validate_catalog."""
        return cls.validate_catalog()

    @classmethod
    def get_translation(
        cls,
        key: str,
        locale: str = "en",
        **kwargs: Any
    ) -> TranslationResult:
        """
        Retrieves localized string by dotted key path (e.g. 'financial.revenue').
        Falls back to English if missing, preserving financial facts safely.
        """
        cls._load_catalogs()
        clean_locale = locale.lower().replace("_", "-").split("-")[0].strip() if locale else cls.DEFAULT_LOCALE

        # 1. Look up in requested locale
        raw_text, resolved_locale, is_fallback = cls._lookup(key, clean_locale)

        # 2. Interpolate protected tokens (amounts, currencies, IDs)
        final_text = cls._interpolate(raw_text, kwargs)

        return TranslationResult(
            text=final_text,
            is_fallback=is_fallback,
            requested_locale=clean_locale,
            resolved_locale=resolved_locale,
            key=key,
        )

    @classmethod
    def _lookup(cls, key: str, locale: str) -> Tuple[str, str, bool]:
        """Resolves key from catalog with fallback hierarchy."""
        parts = key.split(".")

        # Try requested locale
        if locale in cls._CATALOGS:
            val = cls._traverse(cls._CATALOGS[locale], parts)
            if val is not None:
                return str(val), locale, False

        # Fallback to English default
        if cls.DEFAULT_LOCALE in cls._CATALOGS and locale != cls.DEFAULT_LOCALE:
            val = cls._traverse(cls._CATALOGS[cls.DEFAULT_LOCALE], parts)
            if val is not None:
                return str(val), cls.DEFAULT_LOCALE, True

        # Last resort fallback: return key itself
        return key, "unknown", True

    @staticmethod
    def _traverse(node: Any, parts: List[str]) -> Optional[Any]:
        curr = node
        for p in parts:
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            else:
                return None
        return curr

    @staticmethod
    def _interpolate(template: str, kwargs: Dict[str, Any]) -> str:
        """
        Replaces {{placeholder}} tokens with verbatim arguments.
        Preserves numeric values, currency codes, and IDs without transformation.
        """
        if not kwargs:
            return template

        result = template
        for k, v in kwargs.items():
            token = f"{{{{{k}}}}}"
            if token in result:
                result = result.replace(token, str(v))

        return result

    @classmethod
    def validate_catalog(cls) -> Dict[str, Any]:
        """
        Audits translation completeness against the English master catalog.
        Reports missing keys and placeholder discrepancies.
        """
        cls._load_catalogs()
        master = cls._CATALOGS.get(cls.DEFAULT_LOCALE, {})
        master_keys = cls._flatten_keys(master)

        report: Dict[str, Any] = {
            "master_key_count": len(master_keys),
            "catalogs_checked": len(cls._CATALOGS),
            "results": {}
        }

        for lang, cat in cls._CATALOGS.items():
            if lang == cls.DEFAULT_LOCALE:
                continue

            lang_keys = cls._flatten_keys(cat)
            missing = set(master_keys.keys()) - set(lang_keys.keys())
            placeholder_mismatches = []

            for k, master_val in master_keys.items():
                if k in lang_keys:
                    master_tokens = set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", str(master_val)))
                    lang_tokens = set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", str(lang_keys[k])))
                    if master_tokens != lang_tokens:
                        placeholder_mismatches.append({
                            "key": k,
                            "expected_tokens": sorted(list(master_tokens)),
                            "actual_tokens": sorted(list(lang_tokens)),
                        })

            report["results"][lang] = {
                "total_keys": len(lang_keys),
                "completeness_pct": round((len(lang_keys) / len(master_keys)) * 100, 2) if master_keys else 100.0,
                "missing_keys_count": len(missing),
                "missing_keys": sorted(list(missing)),
                "placeholder_mismatches": placeholder_mismatches,
            }

        return report

    @classmethod
    def _flatten_keys(cls, node: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
        flat = {}
        for k, v in node.items():
            full_k = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                flat.update(cls._flatten_keys(v, full_k))
            else:
                flat[full_k] = str(v)
        return flat


# Global shortcut function
def t(key: str, locale: str = "en", **kwargs: Any) -> str:
    """Convenience translation wrapper."""
    return I18nService.get_translation(key, locale=locale, **kwargs).text
