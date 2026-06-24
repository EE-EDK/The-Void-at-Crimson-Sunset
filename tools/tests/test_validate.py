from pathlib import Path
from PIL import Image
from tools.comic.validate import validate


def _strip(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1280, 720), (0, 0, 0)).save(path, "WEBP")


def _ok_manifest(strips_dir):
    _strip(strips_dir / "headache_studio.webp")
    return {"beats": [{"beat": "headache_studio", "slug": "headache_studio",
                       "strip": "assets/comic/strips/act1/headache_studio.webp",
                       "panels": [{"file": "x.jpg", "role": "establish", "alt": "a",
                                   "rect": {"x": 0, "y": 0, "w": 1280, "h": 720}}]}]}


def test_valid_manifest_has_no_errors(tmp_path):
    m = _ok_manifest(tmp_path)
    assert validate(m, tmp_path, [tmp_path / "headache_studio.webp"], tmp_path) == []


def test_missing_rect_is_error(tmp_path):
    m = _ok_manifest(tmp_path)
    del m["beats"][0]["panels"][0]["rect"]
    errs = validate(m, tmp_path, [tmp_path / "headache_studio.webp"], tmp_path)
    assert any("rect" in e for e in errs)


def test_too_many_files_is_error(tmp_path):
    m = _ok_manifest(tmp_path)
    files = [tmp_path / f"f{i}" for i in range(1001)]
    errs = validate(m, tmp_path, files, tmp_path)
    assert any("1000" in e for e in errs)


def test_bad_slug_is_error(tmp_path):
    m = _ok_manifest(tmp_path)
    m["beats"][0]["slug"] = "Bad Slug"
    errs = validate(m, tmp_path, [tmp_path / "headache_studio.webp"], tmp_path)
    assert any("slug" in e for e in errs)
