from __future__ import annotations

from fastapi import APIRouter

from digital_twin_lab.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])
service = ReportService()


@router.get("/latest")
def latest_report() -> dict[str, object]:
    return service.get_latest_report().model_dump(mode="json")
