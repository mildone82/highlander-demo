"""Jinja2-based deterministic renderer.

Presentation is owned by templates + CSS themes; LLM content is passed as data
and escaped by Jinja2 autoescape. Never render raw LLM-authored HTML.
"""

from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import ReportData
from .views import build_comparison, build_full, build_summary

STYLES = ("elegant", "cool", "realistic")
VIEWS = ("summary", "full", "comparison")

_VIEW_BUILDERS = {
    "summary": build_summary,
    "full": build_full,
    "comparison": build_comparison,
}


class ReportRenderer:
    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir is None:
            templates_dir = Path(__file__).resolve().parents[2] / "templates"
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, data: ReportData, style: str, view: str) -> str:
        if style not in STYLES:
            raise ValueError(f"Unknown style {style!r}; expected one of {STYLES}")
        if view not in VIEWS:
            raise ValueError(f"Unknown view {view!r}; expected one of {VIEWS}")

        context = _VIEW_BUILDERS[view](data)
        context.update(
            {
                "style": style,
                "theme_css": f"themes/{style}.css",
                "styles": STYLES,
                "views": VIEWS,
            }
        )
        template = self.env.get_template("views/%s.html.j2" % view)
        return template.render(**context)

    def render_to_file(
        self,
        data: ReportData,
        style: str,
        view: str,
        output_path: Path,
    ) -> Path:
        html = self.render(data, style, view)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        return output_path
