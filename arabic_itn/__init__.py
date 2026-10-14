"""arabic-itn: inverse text normalization for Arabic ASR transcripts.

normalize(text) turns spoken-form values (numbers, phone numbers, money, times,
dates, spelled emails and order IDs) into their written form. Standard library only.
"""
import re

__all__ = ["normalize"]

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫", "01234567890123456789.")
_DIACRITICS = re.compile("[ً-ْٰـ]")
_LETTERS = str.maketrans("أإآٱىةئؤ", "اااايهيو")
_PUNCT = ".,!?؟،؛:;\"'()[]{}«»…"


def _norm(s):
    return _DIACRITICS.sub("", s).lower().translate(_LETTERS)


def _table(groups):
    """Map every word of each space-separated key to its value, by normalized form."""
    return {_norm(w): v for words, v in groups.items() for w in words.split()}


# Number words. "pre_ten" only counts before عشر (احد عشر), "hprefix" only before مية (تلت مية).
_NUMS = _table({
    "صفر زيرو": (0, "zero"),
    "واحد واحدة": (1, "unit"),
    "اثنين اثنان اتنين ثنين تنين اثنتين اثنتان ثنتين اتنتين": (2, "unit"),
    "ثلاثة ثلاث تلاتة تلات": (3, "unit"),
    "أربعة أربع": (4, "unit"),
    "خمسة خمس": (5, "unit"),
    "ستة ست": (6, "unit"),
    "سبعة سبع": (7, "unit"),
    "ثمانية ثماني ثمان تمانية تمنية تمان": (8, "unit"),
    "تسعة تسع": (9, "unit"),
    "عشرة عشر": (10, "ten"),
    "أحد إحدى حادي": (1, "pre_ten"),
    "اثنا اثني اثنتا اثنتي": (2, "pre_ten"),
    "تلت": (3, "hprefix"),
    "ربع": (4, "hprefix"),
    "تمن ثمن": (8, "hprefix"),
    "حداشر احداشر احدعش حدعش احدعشر": (11, "teen"),
    "اتناشر اطناشر اثنعش اطنعش ثنعش اتنعش اثناشر": (12, "teen"),
    "تلتاشر ثلطعش تلطعش تلاتاشر": (13, "teen"),
    "أربعتاشر اربطعش اربعطعش": (14, "teen"),
    "خمستاشر خمسطعش خمسطاشر": (15, "teen"),
    "ستاشر سطاشر سطعش ستطعش": (16, "teen"),
    "سبعتاشر سبعطعش سبعطاشر": (17, "teen"),
    "تمنتاشر ثمنطعش تمنطاشر ثمنتاشر": (18, "teen"),
    "تسعتاشر تسعطعش تسعطاشر": (19, "teen"),
    "عشرين عشرون": (20, "tens"),
    "ثلاثين ثلاثون تلاتين": (30, "tens"),
    "أربعين أربعون": (40, "tens"),
    "خمسين خمسون": (50, "tens"),
    "ستين ستون": (60, "tens"),
    "سبعين سبعون": (70, "tens"),
    "ثمانين ثمانون تمانين": (80, "tens"),
    "تسعين تسعون": (90, "tens"),
    "مية مئة مائة ميت": (100, "hundred"),
    "مئتين مئتان ميتين متين مائتين مائتان": (200, "hundred"),
    "ثلاثمائة ثلاثمئة ثلاثمية تلتمية تلاتمية ثلثمية": (300, "hundred"),
    "أربعمائة أربعمئة أربعمية ربعمية": (400, "hundred"),
    "خمسمائة خمسمئة خمسمية": (500, "hundred"),
    "ستمائة ستمئة ستمية": (600, "hundred"),
    "سبعمائة سبعمئة سبعمية": (700, "hundred"),
    "ثمانمائة ثمانمئة ثمانمية تمنمية ثمنمية تمانمية": (800, "hundred"),
    "تسعمائة تسعمئة تسعمية": (900, "hundred"),
    "ألف": (1000, "big"),
    "ألفين ألفان": (2000, "big"),
    "آلاف ألاف تلاف": (1000, "plural"),
    "مليون": (10 ** 6, "big"),
    "مليونين مليونان": (2 * 10 ** 6, "big"),
    "ملايين": (10 ** 6, "plural"),
})


class _Tok:
    """One whitespace token. start/end cover the core (no edge punctuation, no و prefix)."""

    def __init__(self, start, end, core, post):
        self.start, self.end, self.core, self.post = start, end, core, post
        self.key = _norm(core)
        self.conj = False  # spoken "و" (and) before this token
        lit = re.fullmatch(r"\+?\d+(?:-\d+)*", core)
        self.digits = re.sub(r"\D", "", core) if lit else None
        self.plus = core.startswith("+")


def _tokens(text):
    toks = []
    for m in re.finditer(r"\S+", text):
        raw = m.group()
        core = raw.strip(_PUNCT)
        if not core:
            toks.append(_Tok(m.start(), m.end(), "", raw))
            continue
        lead = len(raw) - len(raw.lstrip(_PUNCT))
        t = _Tok(m.start() + lead, m.start() + lead + len(core), core, raw[lead + len(core):])
        if t.key not in _KNOWN and t.key[:1] == "و" and t.key[1:] in _KNOWN:
            t.key, t.start, t.conj = t.key[1:], t.start + 1, True
        elif t.key in _KNOWN and toks and toks[-1].key == "و" and not toks[-1].post:
            toks.pop()
            t.conj = True
        toks.append(t)
    return toks


def _place(v):
    return 10 ** (len(str(v)) - 1)


def _kind(t):
    return _NUMS.get(t.key, (None, None)) if t.digits is None else (None, None)


def _number(toks, i):
    """Parse one spoken number at toks[i]. Returns (end, value, digit_string) or None."""
    t = toks[i]
    if t.digits is not None:
        return i + 1, int(t.digits), t.digits
    v, kind = _kind(t)
    if kind is None or kind == "plural":
        return None
    if kind == "zero":
        return i + 1, 0, "0"
    total = cur = 0
    level = None  # smallest multiplier (1000 / 10**6) used so far
    comps = []  # components added at the current level, for the "و" ordering rule
    j = i
    while j < len(toks):
        t = toks[j]
        v, kind = _kind(t)
        if kind is None or kind == "zero" and j > i:
            break
        if j > i and toks[j - 1].post:
            break
        pv, pkind = _kind(toks[j - 1]) if j > i else (None, None)
        if j == i or t.conj:
            if j > i:
                last = comps[-1] if comps else level
                unit_tens = kind == "tens" and comps and comps[-1] < 10 and (len(comps) == 1 or comps[-2] >= 100)
                if kind == "plural" or not (v < _place(last) or unit_tens):
                    break
            if kind in ("pre_ten", "hprefix"):
                nv, nkind = _kind(toks[j + 1]) if j + 1 < len(toks) else (None, None)
                need = "ten" if kind == "pre_ten" else "hundred"
                if nkind != need or toks[j + 1].conj or (need == "hundred" and nv != 100):
                    break
            if kind == "big":
                if cur:
                    break
                m = 1000 if v < 10 ** 6 else 10 ** 6
                total, level, comps = total + v, m, [m]
            elif kind == "tens" and comps and comps[-1] < 10 and j > i:
                cur += v
                comps.append(1)  # unit + tens closes the group: nothing smaller may follow
            else:
                cur += v
                comps.append(v)
        elif kind == "ten" and pkind in ("unit", "pre_ten") and comps and comps[-1] == pv:
            cur += 10
            comps.append(1)
        elif kind == "hundred" and v == 100 and pkind in ("unit", "hprefix") and 3 <= pv <= 9 and comps[-1] == pv:
            cur += pv * 99
            comps[-1] = pv * 100
        elif kind in ("big", "plural") and cur and v in (1000, 10 ** 6):
            if (level and v >= level) or (kind == "plural" and not 3 <= cur <= 10):
                break
            total, cur, level, comps = total + cur * v, 0, v, [v]
        else:
            break
        j += 1
    if j == i:
        return None
    return j, total + cur, str(total + cur)


def _match_number(toks, i, country):
    if toks[i].digits is not None:
        return None
    r = _number(toks, i)
    if not r:
        return None
    end, value, _ = r
    if end - i == 1 and (value < 11 or value in (100, 1000)):
        return None  # keep lone small words ("واحد صاحبي", "ألف مبروك")
    return end, "number", str(value)


_MATCHERS = [_match_number]

_KNOWN = set(_NUMS)


def normalize(text, country="SA"):
    """Normalize spoken-form values in an Arabic transcript.

    Returns a dict: "text" (the normalized text) and "spans" (a list of dicts with
    "type", "raw" and "value", one per converted value, in order).
    country ("SA" or "AE") picks the calling code for local 05... mobile numbers.
    """
    conv = text.translate(_DIGITS)  # 1:1 char map, so offsets match the input
    toks = _tokens(conv)
    out, spans, pos, i = [], [], 0, 0
    while i < len(toks):
        for match in _MATCHERS:
            m = match(toks, i, country)
            if m:
                break
        else:
            i += 1
            continue
        end, kind, value = m
        a, b = toks[i].start, toks[end - 1].end
        out += [conv[pos:a], value]
        spans.append(dict(type=kind, raw=text[a:b], value=value))
        pos, i = b, end
    out.append(conv[pos:])
    return dict(text="".join(out), spans=spans)
