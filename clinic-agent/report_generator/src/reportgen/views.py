"""View models: map ReportData into the context each HTML view needs."""

from collections import defaultdict
from typing import Dict, List

from .models import Record, ReportData

RECORD_TYPE_LABELS = {
    "medical_record": "病历",
    "photo": "照片",
    "xray": "X 光",
}

VIEWS = ("summary", "full", "comparison")


def _group_records(records: List[Record]) -> Dict[str, List[Record]]:
    grouped = defaultdict(list)
    for record in records:
        grouped[record.record_type].append(record)
    for items in grouped.values():
        items.sort(key=lambda r: r.recorded_at)
    return grouped


def _timeline(records: List[Record]) -> List[Record]:
    return sorted(records, key=lambda r: r.recorded_at)


def build_summary(data: ReportData) -> dict:
    records = _timeline(data.records)
    return {
        "view": "summary",
        "data": data,
        "recent_records": records[-5:][::-1],
        "record_type_labels": RECORD_TYPE_LABELS,
    }


def build_full(data: ReportData) -> dict:
    return {
        "view": "full",
        "data": data,
        "timeline": _timeline(data.records),
        "grouped": _group_records(data.records),
        "record_type_labels": RECORD_TYPE_LABELS,
    }


def build_comparison(data: ReportData) -> dict:
    by_stage = defaultdict(list)
    for record in data.records:
        by_stage[record.stage].append(record)

    stage_groups = []
    for stage in data.stages:
        stage_records = _timeline(by_stage.get(stage.stage_id, []))
        stage_groups.append(
            {
                "stage": stage,
                "records": stage_records,
                "record_count": len(stage_records),
            }
        )

    return {
        "view": "comparison",
        "data": data,
        "stage_groups": stage_groups,
        "record_type_labels": RECORD_TYPE_LABELS,
    }
