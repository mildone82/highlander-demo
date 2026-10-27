"""Small CLI for one-off rendering.

Usage:
    python -m reportgen --data examples/sample_data.json \
        --style elegant --view full --out outputs/elegant-full.html
"""

import argparse
import json
from pathlib import Path

from .models import Client, Metric, Record, ReportData, Stage
from .renderer import ReportRenderer


def _load(data_path: Path) -> ReportData:
    raw = json.loads(Path(data_path).read_text(encoding="utf-8"))
    raw["client"] = Client(**raw["client"])
    raw["key_metrics"] = [Metric(**m) for m in raw["key_metrics"]]
    raw["records"] = [Record(**r) for r in raw["records"]]
    raw["stages"] = [Stage(**s) for s in raw["stages"]]
    return ReportData(**raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a clinic HTML report")
    parser.add_argument("--data", required=True)
    parser.add_argument("--style", choices=("elegant", "cool", "realistic"), required=True)
    parser.add_argument("--view", choices=("summary", "full", "comparison"), required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    data = _load(Path(args.data))
    ReportRenderer().render_to_file(data, args.style, args.view, Path(args.out))
    print(args.out)


if __name__ == "__main__":
    main()
