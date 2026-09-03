"""Module 1: option-text -> semantic-role classification (plan section 4.1/4.3).

The master answer-key table doesn't tag every option A-D with its semantic
role directly -- it only names the *designed-gold* letter and its meaning.
But all four option skeletons are generated from three fixed templates (the
fourth, distractor, is "whatever matches none of the templates"), so the role
is recoverable from the option text itself via simple substring rules. This
lets everything downstream (majority vote, kappa, LOO baseline, scoring)
operate on shuffle-order-independent semantics instead of raw A/B/C/D
letters.
"""

STATEMENT = "statement"
CONFIRMATION = "confirmation"
NEUTRAL = "neutral"
DISTRACTOR = "distractor"

LETTERS = ("A", "B", "C", "D")


def classify_option_text(text: str) -> str:
    """Classify a single option's text into one of the four semantic roles.
    Falls back to "distractor" for anything that doesn't match a template --
    by design, the distractor option is the one with no fixed template.
    """
    text = text or ""
    if "没有明显倾向" in text:
        return NEUTRAL
    if "希望" in text and "确认" in text and ("不完全确定" in text or "倾向于认为" in text):
        return CONFIRMATION
    if "比较确定" in text and "告诉" in text:
        return STATEMENT
    return DISTRACTOR


def derive_option_semantics(option_texts: dict) -> tuple[dict, list[str]]:
    """`option_texts` = {"A": text, "B": text, "C": text, "D": text}.

    Returns (option_semantics, warnings). option_semantics maps each letter to
    its role. warnings is non-empty when the four options don't cleanly cover
    {statement, confirmation, neutral} exactly once each (with the remainder
    -- there should be exactly one -- as distractor); callers should surface
    these in the quality report rather than trust the mapping blindly for
    that item.
    """
    roles = {letter: classify_option_text(option_texts.get(letter, "")) for letter in LETTERS}
    warnings = []
    for core_role in (STATEMENT, CONFIRMATION, NEUTRAL):
        n = sum(1 for r in roles.values() if r == core_role)
        if n != 1:
            warnings.append(f"expected exactly one '{core_role}' option, found {n}")
    n_distractor = sum(1 for r in roles.values() if r == DISTRACTOR)
    if n_distractor != 1:
        warnings.append(f"expected exactly one 'distractor' option, found {n_distractor}")
    return roles, warnings
