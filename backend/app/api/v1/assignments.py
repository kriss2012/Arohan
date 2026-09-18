from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.user import User, StudentProfile, StudentEnrollment, FacultySubjectAssignment, UserRole
from backend.app.models.assignment import Assignment, AssignmentSubmission, SubmissionFile, AssignmentEvaluation
from backend.app.models.progress import Result, SkillEvidence
from backend.app.schemas.assignment import AssignmentOut, SubmissionOut, EvaluationCreate
from backend.app.services.local_storage_service import LocalStorageService
from backend.app.services.progress_service import ProgressService
from backend.app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/assignments", tags=["Assignments"])

@router.post("/", response_model=AssignmentOut)
async def create_assignment(
    title: str = Form(...),
    subject_id: str = Form(...),
    due_date_iso: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    instructions: Optional[str] = Form(None),
    total_marks: float = Form(100.0),
    passing_marks: float = Form(40.0),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["FACULTY", "HOD", "SUPER_ADMIN"]))
):
    # Verify faculty is assigned to this subject (unless HOD/admin)
    roles_res = await db.execute(select(UserRole.role_name).where(UserRole.user_id == current_user.id))
    user_roles = roles_res.scalars().all()

    if "SUPER_ADMIN" not in user_roles and "HOD" not in user_roles:
        f_assign = await db.execute(
            select(FacultySubjectAssignment).where(
                FacultySubjectAssignment.faculty_id == current_user.id,
                FacultySubjectAssignment.subject_id == subject_id
            )
        )
        if not f_assign.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="You are not authorized to create assignments for this subject.")

    if due_date_iso:
        due_dt = datetime.fromisoformat(due_date_iso.replace("Z", "+00:00"))
    else:
        due_dt = datetime.now(timezone.utc) + timedelta(days=7)

    file_id = None
    if file:
        file_bytes = await file.read()
        file_rec = await LocalStorageService.save_file(
            db=db,
            file_bytes=file_bytes,
            original_filename=file.filename or "assignment.pdf",
            uploaded_by_user_id=current_user.id,
            category="assignments",
            entity_type="ASSIGNMENT"
        )
        file_id = file_rec.id

    asgn = Assignment(
        title=title,
        description=description,
        instructions=instructions,
        subject_id=subject_id,
        faculty_id=current_user.id,
        total_marks=total_marks,
        passing_marks=passing_marks,
        due_date=due_dt,
        file_id=file_id,
        created_by=current_user.id,
        status="PUBLISHED"
    )
    db.add(asgn)
    await db.commit()
    await db.refresh(asgn)
    return asgn

@router.get("/", response_model=List[AssignmentOut])
async def list_assignments(
    subject_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Assignment).where(Assignment.status == "PUBLISHED")
    if subject_id:
        query = query.where(Assignment.subject_id == subject_id)
    
    result = await db.execute(query.order_by(Assignment.due_date.asc()))
    return result.scalars().all()

@router.post("/{assignment_id}/submit", response_model=SubmissionOut)
async def submit_assignment(
    assignment_id: str,
    submission_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["STUDENT"]))
):
    asgn_res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = asgn_res.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check for existing submission
    sub_res = await db.execute(
        select(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.student_id == current_user.id
        )
    )
    submission = sub_res.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    due_dt = assignment.due_date if (assignment.due_date and assignment.due_date.tzinfo) else (assignment.due_date.replace(tzinfo=timezone.utc) if assignment.due_date else now)
    is_late = now > due_dt

    if not submission:
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=current_user.id,
            attempt_number=1,
            submitted_at=now,
            status="LATE" if is_late else "SUBMITTED",
            submission_text=submission_text,
            total_marks=assignment.total_marks
        )
        db.add(submission)
        await db.flush()
    else:
        submission.submission_text = submission_text
        submission.submitted_at = now
        submission.status = "LATE" if is_late else "SUBMITTED"
        submission.attempt_number += 1

    # Save submission file if uploaded
    if file:
        file_bytes = await file.read()
        file_rec = await LocalStorageService.save_file(
            db=db,
            file_bytes=file_bytes,
            original_filename=file.filename or "solution.pdf",
            uploaded_by_user_id=current_user.id,
            category="submissions",
            entity_type="SUBMISSION",
            entity_id=submission.id
        )
        db.add(SubmissionFile(
            submission_id=submission.id,
            file_id=file_rec.id,
            file_type="SOLUTION"
        ))

    await db.commit()
    await db.refresh(submission)
    return submission

@router.get("/{assignment_id}/submissions", response_model=List[SubmissionOut])
async def list_assignment_submissions(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["FACULTY", "HOD", "SUPER_ADMIN"]))
):
    # Verify assignment exists
    asgn_res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = asgn_res.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    result = await db.execute(
        select(AssignmentSubmission)
        .where(AssignmentSubmission.assignment_id == assignment_id)
        .order_by(AssignmentSubmission.submitted_at.desc())
    )
    return result.scalars().all()

@router.post("/submissions/{submission_id}/evaluate", response_model=SubmissionOut)
async def evaluate_submission(
    submission_id: str,
    payload: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["FACULTY", "HOD", "SUPER_ADMIN"]))
):
    sub_res = await db.execute(select(AssignmentSubmission).where(AssignmentSubmission.id == submission_id))
    submission = sub_res.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Fetch parent assignment
    asgn_res = await db.execute(select(Assignment).where(Assignment.id == submission.assignment_id))
    assignment = asgn_res.scalar_one_or_none()

    marks = payload.marks_obtained
    if marks < 0 or marks > submission.total_marks:
        raise HTTPException(status_code=400, detail=f"Marks must be between 0 and {submission.total_marks}")

    pct = round((marks / max(1.0, submission.total_marks)) * 100.0, 2)
    if pct >= 80:
        grade = "A"
    elif pct >= 65:
        grade = "B"
    elif pct >= 50:
        grade = "C"
    elif pct >= 40:
        grade = "D"
    else:
        grade = "F"

    now = datetime.now(timezone.utc)
    submission.marks_obtained = marks
    submission.percentage = pct
    submission.grade = grade
    submission.faculty_feedback = payload.feedback
    submission.evaluated_by = current_user.id
    submission.evaluated_at = now
    submission.status = "EVALUATED"

    # Create / Update Evaluation
    eval_rec = AssignmentEvaluation(
        submission_id=submission.id,
        faculty_id=current_user.id,
        marks_obtained=marks,
        percentage=pct,
        grade=grade,
        feedback=payload.feedback,
        strengths=payload.strengths,
        improvements=payload.improvements,
        evaluated_at=now,
        published_at=now,
        status="PUBLISHED"
    )
    db.add(eval_rec)

    # 1. Store in Results table
    db.add(Result(
        student_id=submission.student_id,
        subject_id=assignment.subject_id,
        assignment_id=assignment.id,
        marks=marks,
        max_marks=submission.total_marks,
        percentage=pct,
        grade=grade,
        published=True,
        published_at=now,
        published_by=current_user.id,
        result_status="PASSED" if pct >= 40.0 else "FAILED"
    ))

    # 2. Record Skill Evidence if topic/subject is linked
    await ProgressService.record_skill_evidence(
        db=db,
        student_id=submission.student_id,
        skill_id="sk-python" if "python" in assignment.title.lower() else "sk-percentages",
        source_type="ASSIGNMENT",
        source_id=submission.id,
        score=pct
    )

    # 3. Recalculate Student Progress
    await ProgressService.recalculate_student_progress(
        db=db,
        student_id=submission.student_id,
        subject_id=assignment.subject_id
    )

    await db.commit()
    await db.refresh(submission)
    return submission

@router.post("/evaluate", response_model=SubmissionOut)
async def evaluate_submission_direct(
    payload: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["FACULTY", "HOD", "SUPER_ADMIN"]))
):
    if not payload.submission_id:
        raise HTTPException(status_code=400, detail="submission_id is required in body.")
    return await evaluate_submission(
        submission_id=payload.submission_id,
        payload=payload,
        db=db,
        current_user=current_user
    )
