"""Annotate the prose HTML with data-beat anchors by matching dialogue lines to paragraphs."""
import re
import unicodedata

_P = re.compile(r"<p\b([^>]*)>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[^>]+>")
_NONWORD = re.compile(r"[^a-z0-9]+")


def normalize(s):
    text = _TAG.sub(" ", s).lower()
    # Decompose accented characters (e.g. é→e, à→a) then strip combining marks
    # so HTML unicode variants match plain-ASCII dialogue text.
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return _NONWORD.sub(" ", text).strip()


def anchor_text(beat):
    for line in beat.get("dialogue", []):
        norm = normalize(line.get("line", ""))
        if len(norm) >= 18:
            return norm
    return None


def annotate_html(html, beats):
    matched, unmatched = [], []
    paragraphs = list(_P.finditer(html))
    norm_paras = [normalize(m.group(2)) for m in paragraphs]
    cursor = 0
    insertions = {}  # paragraph index -> beat name
    for beat in beats:
        text = anchor_text(beat)
        if not text:
            unmatched.append(beat["beat"]); continue
        found = None
        for i in range(cursor, len(paragraphs)):
            if i in insertions or "data-beat" in paragraphs[i].group(1):
                continue
            if text in norm_paras[i]:
                found = i; break
        if found is None:
            unmatched.append(beat["beat"]); continue
        insertions[found] = beat["beat"]
        cursor = found + 1
        matched.append(beat["beat"])
    for i in sorted(insertions, reverse=True):
        m = paragraphs[i]
        html = (html[:m.start()]
                + f'<p data-beat="{insertions[i]}"{m.group(1)}>{m.group(2)}</p>'
                + html[m.end():])
    return html, matched, unmatched
