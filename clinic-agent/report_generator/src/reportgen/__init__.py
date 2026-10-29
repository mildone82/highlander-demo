"""Deterministic HTML report generator for the clinic service.

The generator keeps LLM output (content/narrative) strictly separate from
presentation: the LLM only fills structured JSON slots, while Jinja2 templates
(with autoescape) and per-style CSS themes own layout and safety.
"""

from .models import Client, Metric, Record, ReportData, Stage
from .renderer import ReportRenderer
from .views import VIEWS, build_comparison, build_full, build_summary

__all__ = [
    "Client",
    "Metric",
    "Record",
    "ReportData",
    "Stage",
    "ReportRenderer",
    "VIEWS",
    "build_summary",
    "build_full",
    "build_comparison",
]

__version__ = "0.1.0"
