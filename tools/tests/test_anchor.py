from tools.comic.anchor import normalize, anchor_text, annotate_html


def test_normalize_strips_and_lowers():
    assert normalize("The HEADACHE,  behind his eye!") == "the headache behind his eye"


def test_anchor_text_is_first_dialogue_line():
    beat = {"beat": "b", "dialogue": [{"speaker": "narrator", "line": "The headache had been living."}]}
    assert anchor_text(beat) == "the headache had been living"


def test_anchor_text_none_when_no_dialogue():
    assert anchor_text({"beat": "b", "dialogue": []}) is None


def test_annotate_inserts_data_beat_on_matching_p():
    html = "<article><p>Intro line.</p><p>The headache had been living behind his eye.</p></article>"
    beats = [{"beat": "headache_studio", "dialogue": [{"speaker": "narrator", "line": "The headache had been living"}]}]
    out, matched, unmatched = annotate_html(html, beats)
    assert 'data-beat="headache_studio"' in out
    assert out.count('data-beat=') == 1  # only the matching paragraph
    assert matched == ["headache_studio"] and unmatched == []


def test_unmatched_when_no_paragraph_contains_text():
    html = "<article><p>Nothing relevant.</p></article>"
    beats = [{"beat": "ghost", "dialogue": [{"speaker": "x", "line": "totally absent phrase"}]}]
    out, matched, unmatched = annotate_html(html, beats)
    assert matched == [] and unmatched == ["ghost"]
    assert "data-beat" not in out


def test_forward_cursor_keeps_matches_in_document_order():
    html = ("<article>"
            "<p>Alex first heard the distant hum at dawn.</p>"
            "<p>Years afterward, Alex first heard the distant hum again.</p>"
            "</article>")
    beats = [
        {"beat": "first",  "dialogue": [{"speaker": "n", "line": "Alex first heard the distant hum at dawn"}]},
        {"beat": "second", "dialogue": [{"speaker": "n", "line": "Alex first heard the distant hum again"}]},
    ]
    out, matched, unmatched = annotate_html(html, beats)
    assert matched == ["first", "second"]
    assert out.index('data-beat="first"') < out.index('data-beat="second"')


def test_short_generic_line_is_not_anchored():
    beat = {"beat": "b", "dialogue": [{"speaker": "n", "line": "I remember."}]}
    assert anchor_text(beat) is None
