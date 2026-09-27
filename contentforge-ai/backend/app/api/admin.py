import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, require_roles
from app.models.user import User, UserRole
from ai_services.evaluation.evaluator import get_latest_evaluation_report, run_evaluation_pipeline

logger = logging.getLogger("contentforge.api.admin")

router = APIRouter(prefix="/admin", tags=["Admin & Evaluation"])


@router.get(
    "/evaluation-report",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get latest AI evaluation report",
)
def get_evaluation_report(
    current_user: User = Depends(require_roles([UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN])),
) -> Dict[str, Any]:
    """
    Admin-only endpoint returning the latest AI evaluation quality report.
    Returns composite, faithfulness, answer relevancy, and contextual recall metrics
    evaluated against the golden test dataset.
    """
    logger.info(f"Admin user {current_user.id} requested evaluation report.")
    report = get_latest_evaluation_report()
    return report


@router.post(
    "/evaluation-run",
    response_model=Dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger on-demand evaluation pipeline run",
)
async def trigger_evaluation_run(
    limit: int = Query(4, ge=1, le=16, description="Number of golden documents to evaluate"),
    current_user: User = Depends(require_roles([UserRole.SYSTEM_ADMIN])),
) -> Dict[str, Any]:
    """
    Admin-only endpoint to trigger a fresh evaluation pipeline execution.
    """
    logger.info(f"System admin {current_user.id} triggered fresh evaluation run (limit={limit}).")
    report = await run_evaluation_pipeline(limit=limit, save_results=True)
    return report
