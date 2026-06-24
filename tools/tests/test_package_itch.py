import zipfile
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("pkg_itch", ROOT / "tools/package-itch.py")
pkg_itch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pkg_itch)


def test_zip_has_index_at_root(tmp_path):
    root = tmp_path / "site"
    (root / "assets/comic").mkdir(parents=True)
    (root / "index.html").write_text("<html></html>")
    (root / "assets/comic/act1.comic.json").write_text('{"beats":[]}')
    out = tmp_path / "out.zip"

    rc = pkg_itch.main(["--root", str(root), "--out", str(out), "--skip-validate"])

    assert rc == 0
    with zipfile.ZipFile(out) as z:
        assert "index.html" in z.namelist()
        assert not any(n.startswith("site/") for n in z.namelist())
