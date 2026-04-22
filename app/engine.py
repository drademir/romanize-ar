"""Greedy CharTrans engine — CAMeL Lab ar2phon rules (Apache-2.0 port).

Strips pandas/funcy deps. Implements `translit_simple` rule-only path.
Source: https://github.com/CAMeL-Lab/Arabic-ALA-LC-Romanization
"""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAP_TSV = DATA_DIR / "ar2phon_map.tsv"
EXCEPT_TSV = DATA_DIR / "loc_exceptional_spellings.tsv"

START = "<<<<<"
END = ">>>>>"
CAPSCHAR = "±"


@lru_cache(maxsize=1)
def load_loc_map() -> dict[str, str]:
    with MAP_TSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return {row["Arabic"]: row.get("LOC", "") or "" for row in reader if row.get("Arabic")}


@lru_cache(maxsize=1)
def load_exceptions() -> dict[str, str]:
    out: dict[str, str] = {}
    with EXCEPT_TSV.open(encoding="utf-8") as f:
        next(f, None)  # header
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    return out


def _translit_greedy(token: str, mapdict: dict[str, str]) -> str:
    """Greedy longest-match from start of token, incrementally consuming."""
    s = START + token + END
    keys = sorted(mapdict.keys(), key=len, reverse=True)
    out_parts: list[tuple[str, str]] = []
    i = 0
    nomap = ""
    while i < len(s):
        matched = False
        for k in keys:
            if s.startswith(k, i):
                if nomap:
                    out_parts.append(("NOMAP", nomap))
                    nomap = ""
                val = mapdict[k]
                if val == "~" and out_parts:
                    val = out_parts[-1][1]
                out_parts.append((k, val))
                i += len(k)
                matched = True
                break
        if not matched:
            nomap += s[i]
            i += 1
    if nomap:
        out_parts.append(("NOMAP", nomap))
    return "".join(p[1] for p in out_parts)


def _capitalize_loc(word: str) -> str:
    if word.endswith(CAPSCHAR):
        word = word[:-1]
    if "-" in word and not word.endswith("-") and not word.startswith("-"):
        parts = word.split("-")
        main = parts[-1]
        if main and main[0] in {"ʼ", "ʻ"} and len(main) > 1:
            chars = list(main)
            chars[1] = chars[1].capitalize()
            parts[-1] = "".join(chars)
        elif main:
            parts[-1] = main.capitalize()
        return "-".join(parts)
    if len(word) > 1 and word[0] in {"ʼ", "ʻ"}:
        chars = list(word)
        chars[1] = chars[1].capitalize()
        return "".join(chars)
    return word.capitalize()


def translit_simple(sentence: str) -> str:
    """Rule-only romanization (no morph disambiguation). LOC/ALA-LC output."""
    mapdict = load_loc_map()
    exceptional = load_exceptions()
    out: list[str] = []
    for idx, tok in enumerate(str(sentence).split()):
        tok = exceptional.get(tok, tok)
        romanized = _translit_greedy(tok, mapdict)
        if idx == 0:
            romanized = _capitalize_loc(romanized)
        out.append(romanized)
    return " ".join(out)


# Post-process: recompose (see CAMeL data/make_dataset.py — normalizes hyphens & spacing)
_DOUBLE_HYPHEN = re.compile(r"- +")
_MULTI_SPACE = re.compile(r"\s+")


def recompose(s: str) -> str:
    s = _DOUBLE_HYPHEN.sub("-", s)
    s = _MULTI_SPACE.sub(" ", s).strip()
    return s
