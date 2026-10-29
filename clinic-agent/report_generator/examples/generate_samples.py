"""Render all 3 styles x 3 views from the bundled sample data."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUT = ROOT / "examples" / "output"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reportgen import ReportRenderer
from reportgen.__main__ import _load


def main() -> None:
    data = _load(ROOT / "examples" / "sample_data.json")
    renderer = ReportRenderer(ROOT / "templates")
    for style in ("elegant", "cool", "realistic"):
        for view in ("summary", "full", "comparison"):
            out = OUT / f"{style}-{view}.html"
            renderer.render_to_file(data, style, view, out)
            print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
