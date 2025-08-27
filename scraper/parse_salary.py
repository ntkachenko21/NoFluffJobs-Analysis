import re

HIDDEN_RE = re.compile(r'(sprawdź|do uzgodnienia|negocjowaln|na życzenie|zapytać|hidden|unknown)', re.I)
NUM_RE = re.compile(r'\d{1,3}(?:[ \u00A0]\d{3})*(?:[.,]\d+)?')

def parse_salary_field(s: str, annual_to_month: bool = False):
    if not s or HIDDEN_RE.search(s):
        return "Hidden"

    text = s.strip()
    period_is_year = bool(re.search(r'\b(rocz|rok|year)\b', text, re.I))
    nums = NUM_RE.findall(text)

    def to_int(ns):
        v = ns.replace('\u00A0', ' ').replace(' ', '').replace(',', '.')
        try:
            f = float(v)
        except:
            return None
        if annual_to_month and period_is_year:
            f = f / 12.0
        return int(round(f))

    ints = [to_int(n) for n in nums if to_int(n) is not None]

    # handle plus-sign like "16 000+ PLN" => [16000, None]
    if '+' in text and len(ints) >= 1:
        return [ints[0], None]

    if len(ints) >= 2:
        low, high = min(ints[0], ints[1]), max(ints[0], ints[1])
        return [low, high]
    if len(ints) == 1:
        if re.search(r'\bdo\b', text, re.I):
            return [None, ints[0]]
        if re.search(r'\bod\b', text, re.I):
            return [ints[0], None]
        return [ints[0], ints[0]]
    return "Hidden"
