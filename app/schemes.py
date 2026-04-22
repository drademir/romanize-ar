"""LOC/ALA-LC ↔ IJMES/EI3 post-process.

Core differences (Brill EI3 & IJMES vs Library of Congress ALA-LC):
- IJMES/EI3: final alif maqṣūra → ā (LOC uses á)
- IJMES/EI3: drop final case-ending diacritics (already done at morph stage)
- IJMES/EI3: tāʾ marbūṭa → a (non-construct), at (construct) — same as LOC
- Hamza conventions same: ʾ (initial dropped in IJMES/EI3 word-initial)
- ʿayn same: ʿ (U+02BF)

CAMeL engine emits:
- ʻ (U+02BB modifier letter turned comma) for ʿayn
- ʼ (U+02BC modifier letter apostrophe) for hamza
We normalize to the Unicode chars used in academic publishing.
"""
from __future__ import annotations

import re

# CAMeL → standard academic
_HAMZA_IN = "ʼ"  # U+02BC
_AYN_IN = "ʻ"  # U+02BB
_HAMZA_OUT = "ʾ"  # U+02BE
_AYN_OUT = "ʿ"  # U+02BF


def normalize_unicode(s: str) -> str:
    return s.replace(_HAMZA_IN, _HAMZA_OUT).replace(_AYN_IN, _AYN_OUT)


_FINAL_ALIF_MAQSURA = re.compile(r"á(?=\b|$|[\s\-.,;:!?])")
_WORD_INIT_HAMZA = re.compile(r"(^|[\s\-])ʾ")


def loc_to_ijmes(s: str) -> str:
    """Convert LOC/ALA-LC output to IJMES/EI3."""
    s = normalize_unicode(s)
    # Final alif maqṣūra: á → ā
    s = _FINAL_ALIF_MAQSURA.sub("ā", s)
    # Word-initial hamza dropped in IJMES (al-amr not al-ʾamr; amīr not ʾamīr)
    s = _WORD_INIT_HAMZA.sub(lambda m: m.group(1), s)
    return s


def apply_scheme(s: str, scheme: str) -> str:
    s = normalize_unicode(s)
    scheme = (scheme or "ijmes").lower()
    if scheme in {"ijmes", "ei3"}:
        return loc_to_ijmes(s)
    if scheme in {"ala-lc", "loc", "ala"}:
        return s
    raise ValueError(f"Unknown scheme: {scheme!r}. Use 'ijmes' or 'ala-lc'.")
