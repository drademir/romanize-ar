"""Rule-engine smoke tests (no MLE disambig — tests raw CharTrans + schemes)."""
import pytest

from app.engine import recompose, translit_simple
from app.schemes import apply_scheme, loc_to_ijmes


def rom(text: str, scheme: str = "ijmes") -> str:
    out = recompose(translit_simple(text))
    return apply_scheme(out, scheme)


def test_simple_word():
    # كتاب (undiacritized) → greedy LOC output, not fully accurate without MLE
    result = translit_simple("كتاب")
    assert result  # non-empty
    assert any(c in result for c in "kt")


def test_hamza_normalized():
    # U+02BC → U+02BE
    assert apply_scheme("ʼamīr", "ijmes") == "amīr"  # initial hamza drop
    assert apply_scheme("ʼ", "ala-lc") == "ʾ"


def test_ayn_normalized():
    assert apply_scheme("ʻilm", "ijmes") == "ʿilm"
    assert apply_scheme("ʻilm", "ala-lc") == "ʿilm"


def test_alif_maqsura_final_ijmes():
    # LOC: á (final) → IJMES: ā
    assert loc_to_ijmes("mūsá") == "mūsā"
    assert loc_to_ijmes("hudá") == "hudā"


def test_alif_maqsura_loc_preserved():
    # ALA-LC keeps á
    assert apply_scheme("mūsá", "ala-lc") == "mūsá"


def test_unknown_scheme_raises():
    with pytest.raises(ValueError):
        apply_scheme("x", "buckwalter")


def test_recompose_joins_tokenized_prefix():
    # CAMeL emits "wa- l-" as tokenization marker → should join to "wa-l-"
    assert recompose("wa- l-kitāb") == "wa-l-kitāb"
    assert recompose("al-  kitāb") == "al-kitāb"
    # Normal spacing preserved (no hyphen before)
    assert recompose("kitāb  jadīd") == "kitāb jadīd"


def test_empty_input():
    assert translit_simple("") == ""
