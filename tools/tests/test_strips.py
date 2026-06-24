from pathlib import Path
from PIL import Image
from tools.comic.strips import pack_beat, augment_manifest


def _img(path, color):
    Image.new("RGB", (1280, 720), color).save(path)


def test_pack_beat_stacks_vertically(tmp_path):
    a, b = tmp_path / "a.jpg", tmp_path / "b.jpg"
    _img(a, (255, 0, 0)); _img(b, (0, 255, 0))
    out = tmp_path / "beat.webp"
    rects = pack_beat([a, b], out)
    assert out.exists()
    assert rects == [{"x": 0, "y": 0, "w": 1280, "h": 720},
                     {"x": 0, "y": 720, "w": 1280, "h": 720}]
    assert Image.open(out).size == (1280, 1440)


def test_augment_manifest_adds_strip_and_rects(tmp_path):
    frames = tmp_path / "frames"; frames.mkdir()
    _img(frames / "0001 - establish - headache_studio.jpg", (10, 10, 10))
    strips = tmp_path / "strips"
    manifest = {"act": "I", "title": "t", "beats": [
        {"beat": "headache_studio", "slug": "headache_studio", "panels": [
            {"file": "0001 - establish - headache_studio.jpg", "role": "establish", "alt": "x"}]}]}
    out = augment_manifest(manifest, frames, strips, "assets/comic/strips/act1")
    beat = out["beats"][0]
    assert beat["strip"] == "assets/comic/strips/act1/headache_studio.webp"
    assert beat["strip_w"] == 1280 and beat["strip_h"] == 720
    assert beat["panels"][0]["rect"] == {"x": 0, "y": 0, "w": 1280, "h": 720}
    assert (strips / "headache_studio.webp").exists()
