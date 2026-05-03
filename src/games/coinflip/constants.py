CHOICE_HEADS = "heads"
CHOICE_TAILS = "tails"

CHOICE_MAP = {
    # ==== HEADS ====
    "h": CHOICE_HEADS,
    "head": CHOICE_HEADS,
    "heads": CHOICE_HEADS,

    # sai nhẹ
    "he": CHOICE_HEADS,
    "hea": CHOICE_HEADS,
    "hed": CHOICE_HEADS,
    "heds": CHOICE_HEADS,
    "had": CHOICE_HEADS,

    # loạn chữ
    "eh": CHOICE_HEADS,
    "haed": CHOICE_HEADS,
    "hdae": CHOICE_HEADS,
    "ehads": CHOICE_HEADS,
    "daehs": CHOICE_HEADS,

    # spam / nhầm
    "hh": CHOICE_HEADS,
    "hhh": CHOICE_HEADS,
    "hd": CHOICE_HEADS,
    "hs": CHOICE_HEADS,


    # ==== TAILS ====
    "t": CHOICE_TAILS,
    "tail": CHOICE_TAILS,
    "tails": CHOICE_TAILS,

    # sai nhẹ
    "ta": CHOICE_TAILS,
    "tal": CHOICE_TAILS,
    "tls": CHOICE_TAILS,
    "tais": CHOICE_TAILS,
    "tals": CHOICE_TAILS,

    # loạn chữ
    "at": CHOICE_TAILS,
    "tial": CHOICE_TAILS,
    "liat": CHOICE_TAILS,
    "atil": CHOICE_TAILS,
    "slait": CHOICE_TAILS,

    # spam / nhầm
    "tt": CHOICE_TAILS,
    "ttt": CHOICE_TAILS,
    "tl": CHOICE_TAILS,
    "ts": CHOICE_TAILS,
}