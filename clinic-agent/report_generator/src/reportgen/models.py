"""Plain data containers shared by the pipeline and the renderer."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Client:
    client_id: str
    name: str
    gender: str = ""
    birth_date: str = ""
    clinic_name: str = ""


@dataclass
class Metric:
    label: str
    value: str
    trend: str = "flat"  # up | down | flat
    unit: str = ""


@dataclass
class Record:
    record_id: str
    recorded_at: str
    record_type: str  # medical_record | photo | xray
    title: str
    summary: str
    stage: str = ""
    asset_url: Optional[str] = None
    asset_thumbnail: Optional[str] = None


@dataclass
class Stage:
    stage_id: str
    name: str
    date_range: str
    narrative: str = ""


@dataclass
class ReportData:
    client: Client
    generated_at: str
    summary: str
    key_metrics: List[Metric]
    records: List[Record]
    stages: List[Stage]
    comparison_conclusion: str = ""
