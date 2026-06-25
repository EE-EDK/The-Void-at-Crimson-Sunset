"""Annotate the prose HTML with data-beat anchors by matching dialogue lines to paragraphs."""
import re
import unicodedata
from collections import Counter

_P = re.compile(r"<p\b([^>]*)>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[^>]+>")
_NONWORD = re.compile(r"[^a-z0-9]+")

_STOP = set((
    "the a an and or of to in on at for with as is was were be been being his her its their "
    "it he she they them you your i me my we our this that these those there here then than so "
    "but not no yes if when while what which who whom how why where into out over under again "
    "all any each from by about had has have will would could should did does done just like "
    "alex back down look felt feel knew know something someone toward through still even more "
    "into onto only very much most some other another said say says one two three"
).split())


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


def apply_alignment(html, beats, mapping):
    """Place data-beat anchors at explicit paragraph indices from a curated
    `mapping` ({beat_name: paragraph_index}). One beat per paragraph (a beat whose
    paragraph is taken or out of range is skipped). Returns (html, anchored_count)."""
    html = strip_anchors(html)
    paragraphs = list(_P.finditer(html))
    P = len(paragraphs)
    insertions = {}
    for b in beats:
        pi = mapping.get(b["beat"])
        if pi is None or not (0 <= pi < P) or pi in insertions:
            continue
        insertions[pi] = b["beat"]
    for i in sorted(insertions, reverse=True):
        m = paragraphs[i]
        html = (html[:m.start()]
                + f'<p data-beat="{insertions[i]}"{m.group(1)}>{m.group(2)}</p>'
                + html[m.end():])
    return html, len(insertions)


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


def _tokens(text):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return [w for w in re.findall(r"[a-z0-9]+", text) if len(w) >= 4 and w not in _STOP]


def _beat_signature(beat):
    """(name_tokens, dialogue_tokens, description_tokens) for content matching."""
    name = set(_tokens(beat["beat"].replace("_", " ")))
    dlg = set()
    for d in beat.get("dialogue", []):
        dlg |= set(_tokens(d.get("line", "")))
    desc = set()
    for p in beat.get("panels", []):
        desc |= set(_tokens(p.get("alt", "")))
    return name, dlg, desc


def _content_pins(para_words, norm_paras, beats, max_df=3):
    """High-precision alignment pins, monotonic. A beat is pinned only on a strong,
    unambiguous signal: (a) its verbatim dialogue line appears in a paragraph, or
    (b) one of its beat-name words is GLOBALLY rare (occurs in <= max_df paragraphs,
    e.g. 'starfall', 'kcrm', 'hawking'). Ambiguous words ('black', 'red', 'door')
    occur too widely to pin on. Unpinned beats are interpolated by the caller."""
    P, B = len(para_words), len(beats)
    if not P or not B:
        return {}
    df = Counter()
    postings = {}
    for j, pw in enumerate(para_words):
        for w in pw:
            df[w] += 1
            postings.setdefault(w, []).append(j)

    ats = [anchor_text(b) for b in beats]
    names = [_beat_signature(b)[0] for b in beats]
    max_slope = max(8, 3.0 * P / B)   # plausible paragraphs-per-beat (~3x average)
    pins, used, cursor = {}, set(), 0
    last_b, last_p = 0, 0
    for bi in range(B):
        expected = round(bi * (P - 1) / (B - 1)) if B > 1 else 0
        chosen = None
        at = ats[bi]
        if at:  # verbatim dialogue line — strongest signal
            for j in range(cursor, P):
                if j not in used and at in norm_paras[j]:
                    chosen = j
                    break
        if chosen is None:  # globally-rare beat-name word
            cands = [j for w in names[bi] if df.get(w, 99) <= max_df
                     for j in postings.get(w, []) if j >= cursor and j not in used]
            if cands:
                chosen = min(cands, key=lambda j: (abs(j - expected), j))
        # Reject an implausibly steep jump from the last accepted pin: a single
        # false match must not race the cursor past the middle of the story.
        if chosen is not None and bi > last_b:
            if (chosen - last_p) / (bi - last_b) > max_slope:
                chosen = None
        if chosen is not None:
            pins[bi] = chosen
            used.add(chosen)
            cursor = chosen + 1
            last_b, last_p = bi, chosen
    return pins


def assign_paragraphs(num_beats, num_paras, pins):
    """One distinct paragraph per beat: monotonic, evenly spread, honoring pins.
    Pins are treated as knots; beats between them are interpolated linearly so the
    spread stays even while aligned at every pin."""
    B, P = num_beats, num_paras
    if B <= 0 or P <= 0:
        return []
    # Monotonic knots from pins.
    knots, lastb, lastp = [], -1, -1
    for b in sorted(pins):
        if b > lastb and pins[b] > lastp:
            knots.append((b, pins[b])); lastb, lastp = b, pins[b]
    # Anchor the ends so leading/trailing beats spread to the page extents.
    if not knots or knots[0][0] != 0:
        knots = [(0, 0)] + knots
    if knots[-1][0] != B - 1:
        knots = knots + [(B - 1, P - 1)]
    # Piecewise-linear interpolation between knots.
    raw = [0.0] * B
    for (ba, pa), (bb, pb) in zip(knots, knots[1:]):
        span = (bb - ba) or 1
        for i in range(ba, bb + 1):
            raw[i] = pa + (i - ba) / span * (pb - pa)
    # Round and force strictly-increasing distinct indices within [0, P-1].
    assigned, prev = [], -1
    for i in range(B):
        t = int(round(raw[i]))
        if t <= prev:
            t = prev + 1
        if t > P - 1:
            t = P - 1
        assigned.append(t); prev = t
    return assigned


def distribute_anchors(html, beats, manual_pins=None):
    """Anchor every beat to a distinct paragraph, evenly spread across the prose.
    Text-matched beats (and any manual_pins = [(beat_name, raw_phrase), ...]) act
    as alignment pins; the rest fill in evenly between them. Returns
    (html, anchored_count, paragraph_count)."""
    html = strip_anchors(html)
    paragraphs = list(_P.finditer(html))
    norm_paras = [normalize(m.group(2)) for m in paragraphs]
    para_words = [set(_tokens(_TAG.sub(" ", m.group(2)))) for m in paragraphs]
    P = len(paragraphs)

    # Content-based alignment: pin beats to paragraphs that mention their
    # distinctive keywords (name + dialogue + description), monotonically.
    pins = _content_pins(para_words, norm_paras, beats)
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
