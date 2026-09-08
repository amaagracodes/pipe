"""pipe.lib.shared.locale — a generic BCP-47 locale value type.

Internationalization is a first-class concern here (the whole platform is about
multilingual work), so locale is modeled explicitly rather than passed as loose
strings. A :class:`Locale` is a parsed BCP-47 tag — ``language[-Script][-REGION]``
(e.g. ``en``, ``en-US``, ``zh-Hant``, ``hi-IN``) — with a fallback chain so a
lookup can degrade gracefully (``hi-IN`` → ``hi`` → ``und``).

Mirrors the design of :class:`~pipe.lib.shared.jurisdiction.Jurisdiction`:
immutable, stdlib-only parsing, string-interchangeable. CLDR-correct *formatting*
(numbers/currency/dates) is a separate concern handled where it's needed (via
babel); this type is just the identity + structure.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Locale", "UND"]


@dataclass(frozen=True, slots=True)
class Locale:
    """A parsed BCP-47 locale: language + optional script + optional region.

    ``language`` is a lowercase ISO-639 code, ``script`` a Title-case ISO-15924
    code (e.g. ``Hant``), ``region`` an uppercase ISO-3166-1 code. ``und`` is the
    undetermined language.
    """

    language: str = "und"
    region: str | None = None
    script: str | None = None

    @classmethod
    def parse(cls, value: "str | Locale" = "und") -> "Locale":
        """Parse a BCP-47 tag. Accepts ``_`` or ``-`` separators; tolerant.

        Subtag roles are inferred by shape: 4 letters = script, 2 letters/3
        digits = region, else language. Unknown/empty -> ``und``.
        """
        if isinstance(value, Locale):
            return value
        parts = [p for p in str(value).replace("_", "-").split("-") if p]
        if not parts:
            return cls()
        language = parts[0].lower()
        script: str | None = None
        region: str | None = None
        for sub in parts[1:]:
            if len(sub) == 4 and sub.isalpha():
                script = sub.title()
            elif (len(sub) == 2 and sub.isalpha()) or (len(sub) == 3 and sub.isdigit()):
                region = sub.upper()
        return cls(language=language or "und", region=region, script=script)

    @property
    def tag(self) -> str:
        """Canonical BCP-47 string, e.g. ``"zh-Hant-HK"``."""
        out = self.language
        if self.script:
            out += f"-{self.script}"
        if self.region:
            out += f"-{self.region}"
        return out

    def fallbacks(self) -> list["Locale"]:
        """Degradation chain, most→least specific, ending at ``und``.

        ``zh-Hant-HK`` → ``zh-Hant`` → ``zh`` → ``und``.
        """
        chain: list[Locale] = [self]
        if self.region and self.script:
            chain.append(Locale(self.language, script=self.script))
        if self.script:
            chain.append(Locale(self.language))
        elif self.region:
            chain.append(Locale(self.language))
        if self.language != "und":
            chain.append(Locale("und"))
        # de-dup preserving order
        seen: set[str] = set()
        out: list[Locale] = []
        for loc in chain:
            if loc.tag not in seen:
                seen.add(loc.tag)
                out.append(loc)
        return out

    def __str__(self) -> str:
        return self.tag


#: The undetermined locale.
UND = Locale()
