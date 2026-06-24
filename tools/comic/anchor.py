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
        if norm:
            return norm
    return None


def annotate_html(html, beats):
    matched, unmatched = [], []
    for beat in beats:
        text = anchor_text(beat)
        if not text:
            unmatched.append(beat["beat"]); continue
        hit = None
        for m in _P.finditer(html):
            if "data-beat" in m.group(1):
                continue
            if text in normalize(m.group(2)):
                hit = m; break
        if hit is None:
            unmatched.append(beat["beat"]); continue
        html = (html[:hit.start()]
                + f'<p data-beat="{beat["beat"]}"{hit.group(1)}>{hit.group(2)}</p>'
                + html[hit.end():])
        matched.append(beat["beat"])
    return html, matched, unmatched
