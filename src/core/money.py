"""
Financial Precision and Currency Handling Module.
Enforces integer minor unit representation (e.g., Poisha/Cents) to completely
prevent IEEE 754 floating-point inaccuracies in financial ledgers.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Any


class Money:
    """
    Precision-safe monetary value represented as an integer of minor units.
    Example: 100.50 BDT = 10050 minor units (poisha).
    """

    __slots__ = ("_amount_minor", "_currency")

    def __init__(self, amount_minor: int, currency: str = "BDT") -> None:
        if not isinstance(amount_minor, int):
            raise TypeError(
                f"Minor unit amount must be an integer, got {type(amount_minor).__name__}: {amount_minor}"
            )
        self._amount_minor: int = amount_minor
        self._currency: str = currency.upper()

    @staticmethod
    def get_minor_unit_multiplier(currency: str) -> int:
        """Returns the multiplier between major and minor units (e.g. 100 for BDT/USD/CNY, 1000 for KWD, 1 for JPY)."""
        curr = currency.upper().strip()
        if curr in ("KWD", "BHD", "OMR", "JOD", "TND"):
            return 1000
        if curr in ("JPY", "KRW", "VND", "CLP", "PYG"):
            return 1
        return 100

    @property
    def multiplier(self) -> int:
        return self.get_minor_unit_multiplier(self._currency)

    @property
    def amount_minor(self) -> int:
        """The value in minor currency units (e.g., cents, poisha)."""
        return self._amount_minor

    @property
    def currency(self) -> str:
        """ISO 4217 currency code or standard representation."""
        return self._currency

    @property
    def amount_major(self) -> Decimal:
        """The value in major units as an exact Decimal."""
        return Decimal(self._amount_minor) / Decimal(self.multiplier)

    @classmethod
    def zero(cls, currency: str = "BDT") -> Money:
        """Factory for 0 minor units."""
        return cls(0, currency)

    @classmethod
    def from_minor(cls, amount_minor: int, currency: str = "BDT") -> Money:
        """Create from integer minor units (poisha/cents)."""
        return cls(amount_minor, currency)

    @classmethod
    def from_major(
        cls, amount_major: Union[int, str, Decimal], currency: str = "BDT"
    ) -> Money:
        """
        Create from major units (e.g., "150.75" or Decimal("150.75")).
        Uses ROUND_HALF_UP rounding to exact integer minor units.
        """
        mult = cls.get_minor_unit_multiplier(currency)
        if isinstance(amount_major, float):
            # Convert float to str first to avoid direct binary float representation errors
            dec = Decimal(str(amount_major))
        elif isinstance(amount_major, Decimal):
            dec = amount_major
        elif isinstance(amount_major, (int, str)):
            dec = Decimal(amount_major)
        else:
            raise TypeError(f"Unsupported major amount type: {type(amount_major)}")

        minor_dec = (dec * Decimal(mult)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return cls(int(minor_dec), currency)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return False
        return (
            self._amount_minor == other._amount_minor
            and self._currency == other._currency
        )

    def __lt__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self._amount_minor < other._amount_minor

    def __le__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self._amount_minor <= other._amount_minor

    def __gt__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self._amount_minor > other._amount_minor

    def __ge__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self._amount_minor >= other._amount_minor

    def __add__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self._amount_minor + other._amount_minor, self._currency)

    def __sub__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self._amount_minor - other._amount_minor, self._currency)

    def __mul__(self, scalar: Union[int, Decimal, float]) -> Money:
        if isinstance(scalar, float):
            scalar_dec = Decimal(str(scalar))
        elif isinstance(scalar, (int, Decimal)):
            scalar_dec = Decimal(scalar)
        else:
            raise TypeError(f"Cannot multiply Money by type {type(scalar)}")

        new_minor = (Decimal(self._amount_minor) * scalar_dec).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        return Money(int(new_minor), self._currency)

    def __neg__(self) -> Money:
        return Money(-self._amount_minor, self._currency)

    def __abs__(self) -> Money:
        return Money(abs(self._amount_minor), self._currency)

    def format(self, include_currency: bool = True) -> str:
        """Format as comma-separated major units with appropriate decimal places."""
        major = self.amount_major
        if self.multiplier == 1000:
            formatted = f"{major:,.3f}"
        elif self.multiplier == 1:
            formatted = f"{major:,.0f}"
        else:
            formatted = f"{major:,.2f}"
        if include_currency:
            return f"{formatted} {self._currency}"
        return formatted

    def _assert_same_currency(self, other: Money) -> None:
        if not isinstance(other, Money):
            raise TypeError(f"Expected Money, got {type(other).__name__}")
        if self._currency != other._currency:
            raise ValueError(
                f"Currency mismatch: Cannot compute {self._currency} and {other._currency}"
            )

    def __repr__(self) -> str:
        return f"Money({self._amount_minor} minor units [{self.format()}])"
