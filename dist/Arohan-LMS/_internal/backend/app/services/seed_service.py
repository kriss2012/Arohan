import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.security import get_password_hash
from backend.app.models.user import (
    Institution, Department, AcademicYear, Division, 
    AuthorizedUser, User, Role, Permission, RolePermission, 
    UserRole, StudentProfile, FacultyProfile, StudentEnrollment, FacultySubjectAssignment
)
from backend.app.models.curriculum import Program, Semester, Subject, Unit, Topic, Resource
from backend.app.models.storage import FileRecord
from backend.app.models.assignment import Assignment, AssignmentSubmission, SubmissionFile, AssignmentEvaluation
from backend.app.models.progress import ProgressWeightConfig, StudentProgress, Result, SkillEvidence
from backend.app.models.evidence import Skill, BKTParameter, StudentSkillCompetency, StudentEvent
from backend.app.models.mcat import Question, QuestionOption, MCATBlueprint, MCATExam
from backend.app.models.arohan import PlacementReadinessProfile

async def seed_database(db: AsyncSession) -> None:
    # 1. Check if already seeded
    existing_inst = await db.execute(select(Institution).where(Institution.code == "IMRD"))
    if existing_inst.scalar_one_or_none():
        return

    print("[Seed] Initializing complete IMRD local institutional database...")

    # 2. Roles & Granular Permissions
    roles = [
        "SUPER_ADMIN", "INSTITUTE_ADMIN", "HOD", "FACULTY",
        "EXAM_CONTROLLER", "PLACEMENT_OFFICER", "MENTOR", "STUDENT"
    ]
    for idx, r_name in enumerate(roles, 1):
        db.add(Role(id=idx, name=r_name, description=f"Institutional role: {r_name}"))
    await db.flush()

    permissions_list = [
        ("USER_VIEW", "View user profiles"),
        ("USER_CREATE", "Add new users to allowlist"),
        ("USER_UPDATE", "Update user records"),
        ("ROLE_ASSIGN", "Assign roles to accounts"),
        ("STUDENT_VIEW", "View student academic profiles"),
        ("FACULTY_VIEW", "View faculty profiles"),
        ("ASSIGNMENT_CREATE", "Create and publish assignments"),
        ("ASSIGNMENT_VIEW", "View subject assignments"),
        ("ASSIGNMENT_GRADE", "Grade and evaluate student submissions"),
        ("SUBMISSION_VIEW", "View student submitted files"),
        ("RESULT_VIEW", "View published academic marks"),
        ("RESULT_PUBLISH", "Publish final exam or assignment marks"),
        ("MCAT_CONDUCT", "Start and monitor MCAT sessions"),
        ("BACKUP_CREATE", "Create local database & storage backups"),
        ("BACKUP_RESTORE", "Restore platform from local backup"),
        ("SYSTEM_SETTINGS", "Configure institutional system parameters")
    ]
    for p_name, p_desc in permissions_list:
        db.add(Permission(name=p_name, description=p_desc))
    await db.flush()

    # Map core permissions
    role_perms = [
        ("SUPER_ADMIN", "USER_VIEW"), ("SUPER_ADMIN", "USER_CREATE"), ("SUPER_ADMIN", "ROLE_ASSIGN"),
        ("SUPER_ADMIN", "BACKUP_CREATE"), ("SUPER_ADMIN", "BACKUP_RESTORE"), ("SUPER_ADMIN", "SYSTEM_SETTINGS"),
        ("INSTITUTE_ADMIN", "USER_VIEW"), ("INSTITUTE_ADMIN", "USER_CREATE"), ("INSTITUTE_ADMIN", "BACKUP_CREATE"),
        ("HOD", "STUDENT_VIEW"), ("HOD", "FACULTY_VIEW"), ("HOD", "RESULT_VIEW"),
        ("FACULTY", "ASSIGNMENT_CREATE"), ("FACULTY", "ASSIGNMENT_VIEW"), ("FACULTY", "ASSIGNMENT_GRADE"),
        ("FACULTY", "SUBMISSION_VIEW"), ("FACULTY", "RESULT_PUBLISH"),
        ("STUDENT", "ASSIGNMENT_VIEW"), ("STUDENT", "RESULT_VIEW")
    ]
    for r_name, p_name in role_perms:
        db.add(RolePermission(role_name=r_name, permission_name=p_name))
    await db.flush()

    # 3. Institution, Department, Academic Year
    inst = Institution(
        id="inst-imrd-01",
        name="RC Patel Institute of Management Research and Development, Shirpur",
        code="IMRD"
    )
    db.add(inst)
    await db.flush()

    dept = Department(
        id="dept-ca-01",
        institution_id=inst.id,
        name="Department of Computer Applications",
        code="DCA"
    )
    db.add(dept)
    await db.flush()

    ay = AcademicYear(
        id="ay-2025-2026",
        year_code="2025-2026",
        is_current=True,
        start_date=datetime(2025, 7, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 6, 30, tzinfo=timezone.utc)
    )
    db.add(ay)
    await db.flush()

    # 4. Programs, Semesters, Divisions
    prog_bca = Program(id="prog-bca", department_id=dept.id, name="Bachelor of Computer Applications (BCA)", duration_years=3)
    prog_mca = Program(id="prog-mca", department_id=dept.id, name="Master of Computer Applications (MCA)", duration_years=2)
    db.add_all([prog_bca, prog_mca])
    await db.flush()

    sem3 = Semester(id="sem-bca-3", program_id=prog_bca.id, semester_number=3, academic_year="2025-2026")
    db.add(sem3)
    await db.flush()

    div_a = Division(id="div-bca-3a", semester_id=sem3.id, name="A", academic_year_id=ay.id)
    div_b = Division(id="div-bca-3b", semester_id=sem3.id, name="B", academic_year_id=ay.id)
    db.add_all([div_a, div_b])
    await db.flush()

    # 5. Subjects, Units, Topics, Resources
    sub_dsa = Subject(id="sub-dsa-301", semester_id=sem3.id, name="Data Structures & Algorithms", code="BCA-301", credits=4)
    sub_apt = Subject(id="sub-apt-302", semester_id=sem3.id, name="Quantitative & Logical Aptitude", code="BCA-302", credits=3)
    sub_java = Subject(id="sub-java-303", semester_id=sem3.id, name="Object Oriented Java Programming", code="BCA-303", credits=4)
    db.add_all([sub_dsa, sub_apt, sub_java])
    await db.flush()

    unit_dsa_1 = Unit(id="unit-dsa-1", subject_id=sub_dsa.id, unit_number=1, title="Linear Data Structures: Arrays & Linked Lists")
    db.add(unit_dsa_1)
    await db.flush()

    top_dsa_1 = Topic(
        id="top-dsa-1",
        unit_id=unit_dsa_1.id,
        title="Singly & Doubly Linked Lists",
        learning_objective="Understand node pointers, pointer manipulation, and asymptotic complexity of list traversal.",
        sequence_order=1
    )
    db.add(top_dsa_1)
    await db.flush()

    res_dsa_1 = Resource(
        id="res-dsa-1",
        topic_id=top_dsa_1.id,
        title="Comprehensive Lecture Notes: Linked Lists & Operations",
        resource_type="NOTES",
        content_text="A linked list is a linear data structure where elements are not stored at contiguous memory locations..."
    )
    db.add(res_dsa_1)

    # 6. Authorized Users Allowlist (Strict Institutional Allowlist)
    auth_users_data = [
        ("auth-1", "student1@imrd.ac.in", "Rohan Patil", "STUDENT", "BCA2024-042", "USED"),
        ("auth-2", "student2@imrd.ac.in", "Pooja Chaudhari", "STUDENT", "BCA2024-043", "USED"),
        ("auth-3", "newstudent@imrd.ac.in", "Krishna Patil", "STUDENT", "BCA2025-001", "INVITED"),
        ("auth-4", "faculty1@imrd.ac.in", "Prof. S. N. Patil", "FACULTY", "EMP-DCA-104", "USED"),
        ("auth-5", "hod@imrd.ac.in", "Dr. V. A. Pawar", "HOD", "EMP-DCA-101", "USED"),
        ("auth-6", "controller@imrd.ac.in", "Prof. K. B. Chaudhari", "EXAM_CONTROLLER", "EMP-DCA-102", "USED"),
        ("auth-7", "placement@imrd.ac.in", "Mr. A. R. Shinde", "PLACEMENT_OFFICER", "EMP-DCA-103", "USED"),
        ("auth-8", "mentor@imrd.ac.in", "Dr. M. S. Deshmukh", "MENTOR", "EMP-DCA-105", "USED"),
        ("auth-9", "admin@imrd.ac.in", "Campus Administrator", "INSTITUTE_ADMIN", "EMP-ADM-001", "USED"),
        ("auth-10", "rahul@imrd.ac.in", "Rahul Patil", "STUDENT", "MCA001", "INVITED"),
    ]

    for a_id, email, name, role, eid, st in auth_users_data:
        db.add(AuthorizedUser(
            id=a_id,
            email=email,
            full_name=name,
            intended_role=role,
            department_id=dept.id,
            program_id=prog_bca.id,
            academic_year_id=ay.id,
            division_id=div_a.id,
            student_or_emp_id=eid,
            activation_code="ACT-IMRD-2026" if st == "INVITED" else None,
            status=st
        ))
    await db.flush()

    # 7. Seed Existing Users
    users_data = [
        ("u-student1", "student1@imrd.ac.in", "Student@123", "Rohan", "Patil", "STUDENT"),
        ("u-student2", "student2@imrd.ac.in", "Student@123", "Pooja", "Chaudhari", "STUDENT"),
        ("u-faculty1", "faculty1@imrd.ac.in", "Faculty@123", "Prof. S. N.", "Patil", "FACULTY"),
        ("u-hod1", "hod@imrd.ac.in", "Hod@123", "Dr. V. A.", "Pawar", "HOD"),
        ("u-controller1", "controller@imrd.ac.in", "Exam@123", "Prof. K. B.", "Chaudhari", "EXAM_CONTROLLER"),
        ("u-placement1", "placement@imrd.ac.in", "Placement@123", "Mr. A. R.", "Shinde", "PLACEMENT_OFFICER"),
        ("u-mentor1", "mentor@imrd.ac.in", "Mentor@123", "Dr. M. S.", "Deshmukh", "MENTOR"),
        ("u-admin1", "admin@imrd.ac.in", "Admin@123", "Campus", "Administrator", "INSTITUTE_ADMIN"),
    ]

    for uid, email, raw_pw, fname, lname, r_name in users_data:
        u = User(
            id=uid,
            institution_id=inst.id,
            department_id=dept.id,
            email=email,
            password_hash=get_password_hash(raw_pw),
            first_name=fname,
            last_name=lname,
            status="ACTIVE",
            is_authorized=True,
            is_active=True,
            email_verified=True,
            is_email_verified=True,
            password_created_at=datetime.now(timezone.utc)
        )
        db.add(u)
        db.add(UserRole(user_id=uid, role_name=r_name))
        if uid == "u-admin1":
            db.add(UserRole(user_id=uid, role_name="SUPER_ADMIN"))

    # Profiles
    db.add(StudentProfile(
        user_id="u-student1", student_id="BCA2024-042", roll_number="BCA2024-042",
        program_id=prog_bca.id, academic_year_id=ay.id, semester_id=sem3.id, division_id=div_a.id, current_cgpa=8.24
    ))
    db.add(StudentProfile(
        user_id="u-student2", student_id="BCA2024-043", roll_number="BCA2024-043",
        program_id=prog_bca.id, academic_year_id=ay.id, semester_id=sem3.id, division_id=div_a.id, current_cgpa=7.90
    ))
    db.add(FacultyProfile(
        user_id="u-faculty1", employee_id="EMP-DCA-104", department_id=dept.id,
        designation="Associate Professor", specialization="Algorithms & Data Science"
    ))
    await db.flush()

    # 8. Enrollments & Faculty-Subject Assignments
    db.add(StudentEnrollment(student_id="u-student1", program_id=prog_bca.id, academic_year_id=ay.id, semester_id=sem3.id, division_id=div_a.id))
    db.add(StudentEnrollment(student_id="u-student2", program_id=prog_bca.id, academic_year_id=ay.id, semester_id=sem3.id, division_id=div_a.id))
    db.add(FacultySubjectAssignment(faculty_id="u-faculty1", subject_id=sub_dsa.id, academic_year_id=ay.id, semester_id=sem3.id, division_id=div_a.id))
    db.add(FacultySubjectAssignment(faculty_id="u-faculty1", subject_id=sub_apt.id, academic_year_id=ay.id, semester_id=sem3.id, division_id=div_a.id))
    await db.flush()

    # 9. Progress Weights & Seed Assignment
    db.add(ProgressWeightConfig(
        institution_id=inst.id,
        assignment_weight=0.20,
        assessment_weight=0.25,
        mcat_weight=0.15,
        coding_weight=0.15,
        project_weight=0.15,
        activity_weight=0.10
    ))

    asgn = Assignment(
        id="asgn-dsa-101",
        title="Assignment 1: Linked List Implementation & Reversal",
        description="Implement a Singly Linked List in Java/Python and write an algorithm to reverse it in O(n) time and O(1) auxiliary space.",
        instructions="Submit your documented source code and complexity analysis as a single PDF or solution file.",
        subject_id=sub_dsa.id,
        unit_id=unit_dsa_1.id,
        topic_id=top_dsa_1.id,
        faculty_id="u-faculty1",
        academic_year_id=ay.id,
        semester_id=sem3.id,
        division_id=div_a.id,
        total_marks=100.0,
        passing_marks=40.0,
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        status="PUBLISHED"
    )
    db.add(asgn)
    await db.flush()

    # 10. Skills, MCAT questions & student1 competency
    skills_data = [
        ("sk-percentages", "QUANTITATIVE", "Percentages", "Rate per hundred, fractional multipliers, successive discounts."),
        ("sk-ratio", "QUANTITATIVE", "Ratio & Proportion", "Comparison of quantities, cross-multiplication, partnerships."),
        ("sk-time-work", "QUANTITATIVE", "Time & Work", "Efficiencies, person-day calculation, pipe & cistern."),
        ("sk-series", "LOGICAL", "Number Series", "Arithmetic, geometric, and alternating Fibonacci progression."),
        ("sk-syllogisms", "LOGICAL", "Syllogisms", "Venn diagram logic, categorical statements, conclusions."),
        ("sk-vocab", "VERBAL", "Vocabulary & Synonyms", "Contextual word meaning, antonyms, precise phrasing."),
        ("sk-sentence-corr", "VERBAL", "Sentence Correction", "Subject-verb agreement, modifiers, parallelism."),
        ("sk-tables", "DATA_INTERPRETATION", "Table Analysis", "Tabular data extraction, growth rates, ratios."),
        ("sk-python", "CODING", "Python Fundamentals", "Control flow, list comprehensions, dictionary hashing.")
    ]

    for s_id, s_cat, s_name, s_desc in skills_data:
        db.add(Skill(id=s_id, category=s_cat, name=s_name, description=s_desc))
        db.add(BKTParameter(skill_id=s_id, p_l0=0.10, p_t=0.15, p_s=0.10, p_g=0.20))
    await db.flush()

    db.add(StudentSkillCompetency(student_id="u-student1", skill_id="sk-percentages", mastery_probability=0.34, confidence_score=0.88, evidence_count=9, correct_count=3, incorrect_count=6))
    db.add(StudentSkillCompetency(student_id="u-student1", skill_id="sk-ratio", mastery_probability=0.45, confidence_score=0.82, evidence_count=6, correct_count=3, incorrect_count=3))
    db.add(StudentSkillCompetency(student_id="u-student1", skill_id="sk-series", mastery_probability=0.82, confidence_score=0.92, evidence_count=12, correct_count=10, incorrect_count=2))
    db.add(StudentSkillCompetency(student_id="u-student1", skill_id="sk-syllogisms", mastery_probability=0.72, confidence_score=0.85, evidence_count=8, correct_count=6, incorrect_count=2))
    db.add(StudentSkillCompetency(student_id="u-student1", skill_id="sk-sentence-corr", mastery_probability=0.68, confidence_score=0.80, evidence_count=7, correct_count=5, incorrect_count=2))

    db.add(PlacementReadinessProfile(
        student_id="u-student1",
        technical_score=82.0,
        coding_score=78.5,
        aptitude_score=68.0,
        project_score=85.0,
        consistency_score=90.0,
        overall_readiness_index=80.7,
        evidence_verified=True
    ))

    # MCAT Blueprint and Exam
    blueprint = MCATBlueprint(
        id="bp-diag-2026",
        title="Institutional Diagnostic Aptitude Assessment 2026",
        total_questions=10,
        time_limit_minutes=15,
        distribution_json=json.dumps({"QUANTITATIVE": 4, "LOGICAL": 3, "VERBAL": 2, "DATA_INTERPRETATION": 1})
    )
    db.add(blueprint)
    await db.flush()

    exam = MCATExam(
        id="exam-diag-101",
        blueprint_id=blueprint.id,
        title="MCAT Diagnostic: Quantitative & Analytical Reasoning",
        exam_code="MCAT-2026-DIAG-01",
        mode="DIAGNOSTIC",
        is_published=True
    )
    db.add(exam)
    await db.flush()

    # 10 Questions
    questions_data = [
        ("q-1", "sk-percentages", "QUANTITATIVE", "Percentages", 0.40, "If 25% of a number is 75, what is 40% of the same number?", "Let number be x. 0.25x = 75 => x = 300. 40% of 300 = 120.", [("A", "100", False), ("B", "120", True), ("C", "140", False), ("D", "150", False)]),
        ("q-2", "sk-percentages", "QUANTITATIVE", "Percentages", 0.60, "A student's marks increased from 60 to 75. What is the percentage increase?", "Increase = 15. Pct = (15 / 60) * 100 = 25%.", [("A", "20%", False), ("B", "25%", True), ("C", "15%", False), ("D", "30%", False)]),
        ("q-3", "sk-percentages", "QUANTITATIVE", "Percentages", 0.70, "In an examination, 35% of candidates failed in Quantitative Aptitude and 42% failed in Reasoning. If 15% failed in both, find the percentage of candidates who passed in both.", "Failed = 35 + 42 - 15 = 62%. Passed = 38%.", [("A", "38%", True), ("B", "40%", False), ("C", "42%", False), ("D", "35%", False)]),
        ("q-4", "sk-ratio", "QUANTITATIVE", "Ratio & Proportion", 0.50, "If A : B = 3 : 4 and B : C = 8 : 9, what is A : C?", "A/C = (3/4)*(8/9) = 24/36 = 2/3.", [("A", "1 : 2", False), ("B", "2 : 3", True), ("C", "3 : 4", False), ("D", "4 : 5", False)]),
        ("q-5", "sk-series", "LOGICAL", "Number Series", 0.45, "Find the next number in the series: 3, 7, 15, 31, 63, ?", "Pattern is 2n + 1. 63 * 2 + 1 = 127.", [("A", "125", False), ("B", "126", False), ("C", "127", True), ("D", "128", False)]),
        ("q-6", "sk-series", "LOGICAL", "Number Series", 0.65, "Find the next term in the sequence: 2, 6, 12, 20, 30, 42, ?", "Differences: +4, +6, +8, +10, +12, so next is +14. 42 + 14 = 56.", [("A", "52", False), ("B", "54", False), ("C", "56", True), ("D", "58", False)]),
        ("q-7", "sk-syllogisms", "LOGICAL", "Syllogisms", 0.55, "Statements: All trees are green. All green things are beautiful. Conclusion I: All trees are beautiful. Conclusion II: All beautiful things are trees.", "Conclusion I follows.", [("A", "Only Conclusion I follows", True), ("B", "Only Conclusion II follows", False), ("C", "Both follow", False), ("D", "Neither follows", False)]),
        ("q-8", "sk-sentence-corr", "VERBAL", "Sentence Correction", 0.50, "Choose the grammatically correct sentence: 'Neither the teacher nor the students ____ present in the laboratory.'", "Agrees with closer subject 'students' plural -> 'were'.", [("A", "was", False), ("B", "were", True), ("C", "is", False), ("D", "are being", False)]),
        ("q-9", "sk-vocab", "VERBAL", "Vocabulary & Synonyms", 0.60, "Select the most appropriate synonym for the word: PRAGMATIC", "Pragmatic means practical.", [("A", "Idealistic", False), ("B", "Practical", True), ("C", "Theoretical", False), ("D", "Hesitant", False)]),
        ("q-10", "sk-tables", "DATA_INTERPRETATION", "Table Analysis", 0.55, "In 2024, Sales = $400k. In 2025, Sales = $520k. What was the annual percentage growth rate?", "Growth = (120 / 400) * 100 = 30%.", [("A", "25%", False), ("B", "28%", False), ("C", "30%", True), ("D", "32%", False)])
    ]

    for qid, skid, cat, subcat, diff, qtext, expl, opts in questions_data:
        q = Question(id=qid, skill_id=skid, category=cat, subcategory=subcat, difficulty=diff, question_text=qtext, explanation=expl, status="APPROVED", version=1)
        db.add(q)
        await db.flush()
        for opt_key, opt_text, is_corr in opts:
            db.add(QuestionOption(id=f"{qid}-{opt_key.lower()}", question_id=q.id, option_key=opt_key, option_text=opt_text, is_correct=is_corr))

    await db.commit()
    print("[Seed] Full institutional database successfully seeded.")
