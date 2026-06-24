from tools.comic.narration import build_index

SHOTS = [
    {"shot_id": "S1-01", "beats": ["headache_studio/entry", "jen_voice/exit"]},
    {"shot_id": "S1-99", "beats": ["far_future/entry"]},
]


def test_ready_shot_gets_audio_path():
    idx = build_index(SHOTS, {"S1-01"}, "assets/comic/narration/act1")
    s = idx["shots"][0]
    assert s["status"] == "ready"
    assert s["audio"] == "assets/comic/narration/act1/S1-01.mp3"
    assert s["beats"] == ["headache_studio", "jen_voice"]


def test_pending_shot_has_no_audio():
    idx = build_index(SHOTS, {"S1-01"}, "assets/comic/narration/act1")
    s = idx["shots"][1]
    assert s["status"] == "pending" and s["audio"] is None


def test_beat_to_shot_maps_each_beat():
    idx = build_index(SHOTS, {"S1-01"}, "assets/comic/narration/act1")
    assert idx["beat_to_shot"]["headache_studio"] == "S1-01"
    assert idx["beat_to_shot"]["far_future"] == "S1-99"
