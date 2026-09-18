from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.mcat import MCATExam, MCATAttempt, MCATIntegrityEvent
from backend.app.api.deps import require_roles

router = APIRouter(prefix="/exam-controller", tags=["Examination Controller"])

@router.get("/live-monitors")
async def get_live_exam_monitors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["EXAM_CONTROLLER", "SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    # Fetch all attempts with their status breakdown
    attempts_res = await db.execute(
        select(
            MCATAttempt.id,
            MCATAttempt.student_id,
            MCATAttempt.status,
            MCATAttempt.remaining_seconds,
            MCATAttempt.score_percentage,
            MCATAttempt.integrity_signal_count,
            User.first_name,
            User.last_name,
            User.email
        )
        .join(User, MCATAttempt.student_id == User.id)
    )
    rows = attempts_res.all()

    candidates = []
    status_counts = {"STARTED": 0, "PAUSED": 0, "SUBMITTED": 0, "AUTO_EVALUATED": 0}
    severity_totals = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    for r in rows:
        att_id, s_id, status, rem, score, sig_count, fname, lname, email = r
        status_counts[status] = status_counts.get(status, 0) + 1
        candidates.append({
            "attempt_id": att_id,
            "student_id": s_id,
            "student_name": f"{fname} {lname}",
            "student_email": email,
            "status": status,
            "remaining_seconds": rem,
            "score_percentage": score,
            "integrity_signal_count": sig_count
        })

    # Recent integrity events
    ev_res = await db.execute(
        select(MCATIntegrityEvent).order_by(desc(MCATIntegrityEvent.timestamp)).limit(10)
    )
    events = [
        {
            "id": ev.id,
            "attempt_id": ev.attempt_id,
            "event_type": ev.event_type,
            "severity": ev.severity,
            "timestamp": ev.timestamp.isoformat(),
            "details": ev.details_json
        }
        for ev in ev_res.scalars().all()
    ]

    for ev in events:
        sev = ev["severity"]
        severity_totals[sev] = severity_totals.get(sev, 0) + 1

    return {
        "active_candidates_count": len(candidates),
        "status_distribution": status_counts,
        "integrity_signal_severity": severity_totals,
        "candidates": candidates,
        "recent_integrity_signals": events
    }
