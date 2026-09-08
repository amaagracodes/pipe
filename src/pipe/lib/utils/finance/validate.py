"""pipe.lib.utils.finance.validate — pure banking/KYC validators.

Checksum validators useful across finance, banking, and legal/KYC contexts.
No network, deterministic; each returns a bool.
"""

from __future__ import annotations

from pipe.lib.core import Pipe

__all__ = ["LuhnCheck", "IBANCheck"]


class LuhnCheck(Pipe):
    """Validate a number (e.g. credit card) with the Luhn checksum. -> bool.

    Ignores spaces/hyphens; any other non-digit content yields ``False``.
    """

    def forward(self, data: str) -> bool:
        raw = str(data)
        if any(c not in " -" and not c.isdigit() for c in raw):
            return False
        digits = [c for c in raw if c.isdigit()]
        if len(digits) < 2:
            return False
        total = 0
        for i, ch in enumerate(reversed(digits)):
            d = int(ch)
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        return total % 10 == 0


class IBANCheck(Pipe):
    """Validate an IBAN via the ISO 7064 mod-97 checksum. -> bool.

    Ignores spaces and case. Structural-length + mod-97 test; does not verify
    country-specific BBAN layouts (kept generic).
    """

    def forward(self, data: str) -> bool:
        s = "".join(str(data).split()).upper()
        if not (15 <= len(s) <= 34) or not s[:2].isalpha() or not s[2:4].isdigit():
            return False
        rearranged = s[4:] + s[:4]
        digits = "".join(str(int(ch, 36)) if ch.isalpha() else ch for ch in rearranged)
        if not digits.isdigit():
            return False
        return int(digits) % 97 == 1
