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


# --- Even distribution: anchor EVERY beat across the prose, one image per stop ---

def strip_anchors(html):
    """Remove any existing data-beat attributes so we can re-anchor cleanly."""
    return re.sub(r'\s+data-beat="[^"]*"', "", html)


def _text_pins(norm_paras, beats):
    """Forward-cursor text matches -> {beat_index: paragraph_index} (monotonic)."""
    pins = {}
    used = set()
    cursor = 0
    for bi, beat in enumerate(beats):
        text = anchor_text(beat)
        if not text:
            continue
        for i in range(cursor, len(norm_paras)):
            if i in used:
                continue
            if text in norm_paras[i]:
                pins[bi] = i
                used.add(i)
                cursor = i + 1
                break
    return pins


def _phrase_pin(norm_paras, phrase):
    """First paragraph index whose normalized text contains `phrase` (already normalized)."""
    for i, np in enumerate(norm_paras):
        if phrase and phrase in np:
            return i
    return None


def assign_paragraphs(num_beats, num_paras, pins):
    """One distinct paragraph per beat: monotonic, evenly spread, honoring pins."""
    if num_beats <= 0 or num_paras <= 0:
        return []
    denom = (num_beats - 1) or 1
    targets = []
    for i in range(num_beats):
        targets.append(pins[i] if i in pins else round(i * (num_paras - 1) / denom))
    assigned, prev = [], -1
    for i in range(num_beats):
        t = targets[i]
        if t <= prev:
            t = prev + 1
        if t >= num_paras:
            t = num_paras - 1
        assigned.append(t)
        prev = t
    return assigned


def distribute_anchors(html, beats, manual_pins=None):
    """Anchor every beat to a distinct paragraph, evenly spread across the prose.
    Text-matched beats (and any manual_pins = [(beat_name, raw_phrase), ...]) act
    as alignment pins; the rest fill in evenly between them. Returns
    (html, anchored_count, paragraph_count)."""
    html = strip_anchors(html)
    paragraphs = list(_P.finditer(html))
    norm_paras = [normalize(m.group(2)) for m in paragraphs]
    P = len(paragraphs)

    pins = _text_pins(norm_paras, beats)
    name_to_index = {b["beat"]: i for i, b in enumerate(beats)}
    for beat_name, phrase in (manual_pins or []):
        bi = name_to_index.get(beat_name)
        if bi is None:
            continue
        pi = _phrase_pin(norm_paras, normalize(phrase))
        if pi is not None:
            pins[bi] = pi

    # Keep only monotonic pins (a later beat must map to a later paragraph).
    clean, last = {}, -1
    for bi in sorted(pins):
        if pins[bi] > last:
            clean[bi] = pins[bi]
            last = pins[bi]

    assigned = assign_paragraphs(len(beats), P, clean)
    insertions = {pi: beats[bi]["beat"] for bi, pi in enumerate(assigned)}
    for i in sorted(insertions, reverse=True):
        m = paragraphs[i]
        html = (html[:m.start()]
                + f'<p data-beat="{insertions[i]}"{m.group(1)}>{m.group(2)}</p>'
                + html[m.end():])
    return html, len(insertions), P
