"""arabic-itn: inverse text normalization for Arabic ASR transcripts.

normalize(text) turns spoken-form values (numbers, phone numbers, money, times,
dates, spelled emails and order IDs) into their written form. Standard library only.
"""
import datetime
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


_PLUS = _table(dict.fromkeys(["زائد زايد plus بلس"], 1))
_REPEAT = _table(dict(zip(["دبل دوبل double", "تريبل تربل triple"], [2, 3])))
_CODES = dict(SA="966", AE="971")


def _e164(d, plus, country):
    """Saudi / UAE mobile digit string -> E.164, else None."""
    if d.startswith("00"):
        d, plus = d[2:], True
    if plus or d[:3] in ("966", "971"):
        cc, nat = d[:3], d[3:]
        if cc not in ("966", "971"):
            return None
        if nat.startswith("0"):
            nat = nat[1:]
    elif re.fullmatch(r"05\d{8}", d):
        cc, nat = _CODES[country], d[1:]
    else:
        return None
    return "+" + cc + nat if re.fullmatch(r"5\d{8}", nat) else None


def _match_digits(toks, i, country):
    """Phone numbers and digit-by-digit runs ("واحد اتنين تلاتة" -> 123)."""
    j = i
    plus = toks[i].key in _PLUS
    if plus:
        j += 1
    parts, single, literal = [], True, False
    while j < len(toks):
        t = toks[j]
        if parts and (t.conj or toks[j - 1].post.strip("،,-")):
            break
        n = _REPEAT.get(t.key)
        if n:
            r = _number(toks, j + 1) if j + 1 < len(toks) else None
            if not r or len(r[2]) != 1 or toks[j + 1].conj:
                break
            parts.append(r[2] * n)
            j = r[0]
            continue
        r = _number(toks, j)
        if not r:
            break
        end, value, d = r
        if t.digits is not None:
            literal = True
        elif end - j > 1 or len(d) > 1:
            single = False  # grouped speech like "مية وتلاتة وعشرين"
        parts.append(d)
        j = end
    if not parts:
        return None
    d = "".join(parts)
    if len(parts) > 1 or plus or literal:
        phone = _e164(d, plus or toks[i].plus, country)
        if phone:
            return j, "phone", phone
    if len(parts) > 1 and single and not literal and len(d) >= 3:
        return j, "digits", d
    return None


_CODES4 = ["SAR", "AED", "EGP", "USD"]
_CURRENCY = _table(dict(zip(["ريال ريالات ريالا", "درهم دراهم درهما", "جنيه جنيهات جنيها", "دولار دولارات دولارا"], _CODES4)))
_DUAL = _table(dict(zip(["ريالين ريالان", "درهمين درهمان", "جنيهين جنيهان", "دولارين دولاران"], _CODES4)))
_SUBUNIT = _table(dict(zip(["هللة هللات هلل", "فلس فلوس فلسا", "قرش قروش قرشا", "سنت سنتات"], _CODES4)))
_CUR_ADJ = _table(dict.fromkeys(["سعودي سعودية إماراتي مصري أمريكي امريكي"], 1))


def _match_money(toks, i, country):
    """Money: "ميتين وخمسين ريال" -> 250 SAR, "عشرة ريال وخمسين هللة" -> 10.50 SAR."""
    t, n = toks[i], len(toks)
    bare = False
    if t.key in _DUAL:
        amount, code, j = 2, _DUAL[t.key], i + 1
    elif t.key in _CURRENCY:  # "جنيه وخمسين قرش": only with a subunit after it
        amount, code, j, bare = 1, _CURRENCY[t.key], i + 1, True
    else:
        r = _number(toks, i)
        if not r or r[0] >= n or toks[r[0] - 1].post:
            return None
        unit = toks[r[0]].key
        if unit in _SUBUNIT and r[1] < 100:
            return r[0] + 1, "money", "0.%02d %s" % (r[1], _SUBUNIT[unit])
        if unit not in _CURRENCY:
            return None
        amount, code, j = r[1], _CURRENCY[unit], r[0] + 1
    if j < n and toks[j].key in _CUR_ADJ and not toks[j - 1].post:
        j += 1
    cents = None
    if j < n and toks[j].conj and not toks[j - 1].post:
        r = _number(toks, j)
        if r and r[1] < 100 and r[0] < n and _SUBUNIT.get(toks[r[0]].key) == code:
            cents, j = r[1], r[0] + 1
    if cents is None:
        return None if bare else (j, "money", "%d %s" % (amount, code))
    return j, "money", "%d.%02d %s" % (amount, cents, code)


_TEN = {"عشر", "عشره"}
_ORD = _table(dict(zip([
    "الأول أول الواحدة الحادي الحادية", "الثاني الثانية", "الثالث الثالثة", "الرابع الرابعة",
    "الخامس الخامسة", "السادس السادسة", "السابع السابعة", "الثامن الثامنة", "التاسع التاسعة",
    "العاشر العاشرة", "العشرين", "الثلاثين"], list(range(1, 11)) + [20, 30])))


def _ordinal(toks, j):
    """"الخامس" / "الحادي عشر" / "الخامس والعشرين" -> (end, value)."""
    v, end = _ORD[toks[j].key], j + 1
    if v < 10 and end < len(toks) and not toks[j].post:
        nxt = toks[end]
        if nxt.key in _TEN and not nxt.conj:
            v, end = v + 10, end + 1
        elif nxt.conj and nxt.key in ("العشرين", "الثلاثين"):
            v, end = v + _ORD[nxt.key], end + 1
    return end, v


_FRACTION = _table(dict(zip(["نص نصف النص النصف", "ربع الربع ربعا", "ثلث الثلث ثلثا تلت التلت"], [30, 15, 20])))
_MINUS = _table(dict.fromkeys(["إلا الا غير"], 1))
_MINUTE = _table(dict.fromkeys(["دقيقة دقايق دقائق"], 1))
_PERIOD = _table(dict(zip([
    "الصبح الصباح صباحا الفجر فجرا",
    "الظهر الضهر ظهرا",
    "العصر عصرا المغرب المسا المساء مساء مسا بالمسا",
    "بالليل الليل ليلا"], ["am", "noon", "pm", "night"])))


def _match_time(toks, i, country):
    """"الساعة تلاتة ونص العصر" -> 15:30. Needs "الساعة" before it or a period word after it."""
    n, t = len(toks), toks[i]
    if t.conj:
        return None
    if t.key in _ORD:
        j, h = _ordinal(toks, i)
    elif t.digits is not None and len(t.digits) <= 2:
        j, h = i + 1, int(t.digits)
    elif _kind(t)[1] in ("unit", "ten", "teen"):
        j, h = i + 1, _kind(t)[0]
    else:
        return None
    if not 1 <= h <= (23 if t.digits else 12):
        return None

    def at(k):
        return toks[k] if k < n and not toks[k - 1].post else None

    m = 0
    nxt = at(j)
    if nxt and nxt.conj and nxt.key in _FRACTION:
        m, j = _FRACTION[nxt.key], j + 1
        nx = at(j)
        if m == 30 and nx and (nx.conj or nx.key in _MINUS):  # "ونص وخمسة" 35, "ونص الا خمسة" 25
            k = j if nx.conj else j + 1
            r = _number(toks, k) if k < n else None
            if r and r[1] in (5, 10):
                m, j = m + (r[1] if nx.conj else -r[1]), r[0]
    elif nxt and nxt.conj:
        r = _number(toks, j)
        if r and 1 <= r[1] <= 59:
            m, j = r[1], r[0]
            if at(j) and toks[j].key in _MINUTE:
                j += 1
    elif nxt and nxt.key in _MINUS and j + 1 < n:
        x = toks[j + 1]
        if _FRACTION.get(x.key) in (15, 20):
            d, j = _FRACTION[x.key], j + 2
        else:
            r = _number(toks, j + 1)
            d = r[1] if r and 1 <= r[1] <= 29 else 0
            if d:
                j = r[0] + (1 if at(r[0]) and toks[r[0]].key in _MINUTE else 0)
        if d:
            h, m = (h - 1) or 12, 60 - d
    period = _PERIOD.get(at(j).key) if at(j) else None
    if period:
        j += 1
    elif not (i > 0 and toks[i - 1].key == "الساعه" and not toks[i - 1].post):
        return None
    if period == "am" and h == 12:
        h = 0
    elif period == "pm" and h < 12 or period == "noon" and h <= 5:
        h += 12
    elif period == "night":
        h = h + 12 if 6 <= h <= 11 else 0 if h == 12 else h
    return j, "time", "%02d:%02d" % (h, m)


_WEEKDAY = _table(dict.fromkeys(["السبت الأحد الإثنين الاتنين الثلاثاء الثلاثا التلات الأربعاء الخميس الجمعة"], 1))
_MONTHS = _table(dict(zip([
    "يناير", "فبراير شباط", "مارس آذار", "أبريل نيسان", "مايو أيار", "يونيو يونيه حزيران",
    "يوليو يوليه تموز", "أغسطس آب", "سبتمبر أيلول", "أكتوبر", "نوفمبر", "ديسمبر"], range(1, 13))))
_MONTH2 = dict(zip([("كانون", "الثاني"), ("تشرين", "الاول"), ("تشرين", "الثاني"), ("كانون", "الاول")], [1, 10, 11, 12]))


def _month(toks, j):
    n = len(toks)
    if j >= n:
        return None
    t = toks[j]
    if t.key in _MONTHS:
        return j + 1, _MONTHS[t.key]
    if j + 1 < n and (t.key, toks[j + 1].key) in _MONTH2:
        return j + 2, _MONTH2[t.key, toks[j + 1].key]
    if t.key == "شهر" and j + 1 < n:
        r = _number(toks, j + 1)
        if r and 1 <= r[1] <= 12:
            return r[0], r[1]
    return None


def _match_date(toks, i, country):
    """[يوم الخميس] خمسة عشر [من] أكتوبر [سنة] ألفين وستة وعشرين -> 2026-10-15. Year required."""
    n, j = len(toks), i
    if toks[j].key == "يوم" and j + 1 < n and toks[j + 1].key in _WEEKDAY:
        j += 1
    if toks[j].key in _WEEKDAY:
        j += 1
    if j >= n:
        return None
    if toks[j].key in _ORD:
        j, day = _ordinal(toks, j)
    else:
        r = _number(toks, j)
        if not r:
            return None
        j, day = r[0], r[1]
    if j < n and toks[j].key == "من":
        j += 1
    r = _month(toks, j)
    if not r:
        return None
    j, month = r
    if j < n and toks[j].key in ("سنه", "عام"):
        j += 1
    r = _number(toks, j) if j < n else None
    if not r or not 1900 <= r[1] <= 2100:
        return None
    try:
        d = datetime.date(r[1], month, day)
    except ValueError:
        return None
    return r[0], "date", d.isoformat()


_MATCHERS = [_match_date, _match_time, _match_money, _match_digits, _match_number]

_KNOWN = (set(_NUMS) | set(_PLUS) | set(_REPEAT) | set(_CURRENCY) | set(_DUAL) | set(_SUBUNIT)
          | set(_ORD) | set(_FRACTION))


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
