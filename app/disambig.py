"""camel-tools MLE disambiguator wrapper — lazy-loaded, optional.

If camel-tools + data model not installed, `disambiguate()` returns None
and the caller falls back to rule-only `translit_simple`.

Data bootstrap (Dockerfile):
    camel_data -i disambig-mle-calima-msa-r13
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

_disambiguator = None
_unavailable = False


def _get_disambiguator():
    global _disambiguator, _unavailable
    if _disambiguator is not None or _unavailable:
        return _disambiguator
    try:
        from camel_tools.disambig.mle import MLEDisambiguator
        _disambiguator = MLEDisambiguator.pretrained()
        log.info("MLEDisambiguator loaded")
    except Exception as e:  # ImportError or data missing
        log.warning("camel-tools disambiguator unavailable: %s", e)
        _unavailable = True
    return _disambiguator


def diacritize(sentence: str) -> str | None:
    """Return diacritized Arabic sentence, or None if camel-tools unavailable."""
    disamb = _get_disambiguator()
    if disamb is None:
        return None
    try:
        from camel_tools.tokenizers.word import simple_word_tokenize
        tokens = simple_word_tokenize(sentence)
        if not tokens:
            return sentence
        analyses = disamb.disambiguate(tokens)
        out = []
        for a in analyses:
            if a.analyses:
                diac = a.analyses[0].analysis.get("diac") or a.word
            else:
                diac = a.word
            out.append(diac)
        return " ".join(out)
    except Exception as e:
        log.warning("diacritize failed: %s", e)
        return None
