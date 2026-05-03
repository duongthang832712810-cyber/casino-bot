from src.core.constants import RESULT_HOUSE


CHOICE_BIG = "big"
CHOICE_SMALL = "small"

STATUS_BETTING = "betting"
STATUS_RESOLVED = "resolved"

CHOICE_ALIASES = {
    "big": CHOICE_BIG,
    "b": CHOICE_BIG,
    "tai": CHOICE_BIG,
    "t": CHOICE_BIG,
    "small": CHOICE_SMALL,
    "s": CHOICE_SMALL,
    "xiu": CHOICE_SMALL,
    "x": CHOICE_SMALL,
}

CHOICE_DISPLAY = {
    CHOICE_BIG: "Big",
    CHOICE_SMALL: "Small",
    RESULT_HOUSE: "House wins",
}
