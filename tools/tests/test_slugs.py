from tools.comic.slugs import slugify


def test_lowercases_and_replaces_spaces():
    assert slugify("Section Break I") == "section_break_i"


def test_strips_punctuation_to_underscore():
    assert slugify("key-object ANCHOR (bow + lowest string)") == "key-object_anchor_bow_lowest_string"


def test_collapses_and_trims_underscores():
    assert slugify("  Iris  Kohler's   viola  ") == "iris_kohler_s_viola"


def test_keeps_existing_beat_ids_stable():
    assert slugify("headache_studio") == "headache_studio"
