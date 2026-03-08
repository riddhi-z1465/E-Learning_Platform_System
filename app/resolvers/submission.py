from typing import List
from db import get_session, next_id
from app.types import Submission, SubmitAssessmentInput, SubmissionResult, Certificate
from app.utils import recalculate_progress

def get_submissions(student_id: int) -> List[Submission]:
    with get_session() as session:
        rows = session.run(
            """
            MATCH (s:Student {id:$sid})-[:HAS_SUBMISSION]->(sub:Submission)
                  -[:FOR_ASSESSMENT]->(a:Assessment)
            RETURN sub, a.id AS aid, s.id AS sid
            """,
            sid=student_id,
        ).data()
        return [Submission(id=r["sub"]["id"], assessment_id=r["aid"],
                           student_id=r["sid"],
                           marks_obtained=r["sub"]["marks_obtained"])
                for r in rows]

def get_completion_certificate(student_id: int, course_id: int) -> Certificate:
    with get_session() as session:
        student_r = session.run(
            "MATCH (s:Student {id:$id}) RETURN s", id=student_id
        ).single()
        if not student_r:
            raise ValueError(f"Student {student_id} not found")

        course_r = session.run(
            "MATCH (c:Course {id:$id}) RETURN c", id=course_id
        ).single()
        if not course_r:
            raise ValueError(f"Course {course_id} not found")

        enroll_r = session.run(
            """
            MATCH (s:Student {id:$sid})-[:HAS_ENROLLMENT]->(e:Enrollment)
                  -[:FOR_COURSE]->(c:Course {id:$cid})
            RETURN e
            """,
            sid=student_id, cid=course_id,
        ).single()
        if not enroll_r:
            raise ValueError("Student is not enrolled in this course")

        marks_r = session.run(
            """
            MATCH (c:Course {id:$cid})-[:HAS_ASSESSMENT]->(a:Assessment)
            OPTIONAL MATCH (s:Student {id:$sid})-[:HAS_SUBMISSION]->(sub:Submission)
                           -[:FOR_ASSESSMENT]->(a)
            RETURN sum(a.total_marks)    AS max_score,
                   sum(sub.marks_obtained) AS total_score,
                   count(a)              AS total_assessments,
                   count(sub)            AS submitted_count
            """,
            sid=student_id, cid=course_id,
        ).single()

        max_score    = float(marks_r["max_score"] or 0)
        total_score  = float(marks_r["total_score"] or 0)
        total_asmts  = marks_r["total_assessments"]
        submitted    = marks_r["submitted_count"]

        percentage = round((total_score / max_score * 100), 2) if max_score > 0 else 0.0
        enrollment = enroll_r["e"]
        is_eligible = (
            enrollment["status"] == "completed"
            and submitted == total_asmts
        )

        return Certificate(
            student_name=student_r["s"]["name"],
            course_title=course_r["c"]["title"],
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            is_eligible=is_eligible,
        )

def submit_assessment(input: SubmitAssessmentInput) -> SubmissionResult:
    """
    Submit marks for an assessment.
    Validations:
      • Assessment must exist
      • Parent course must NOT be archived
      • Student must be enrolled (and not dropped)
      • No duplicate submission
      • marks_obtained <= total_marks
    Auto-recalculates progress and auto-completes enrollment at 100%.
    """
    with get_session() as session:
        asmt_r = session.run(
            """
            MATCH (c:Course)-[:HAS_ASSESSMENT]->(a:Assessment {id:$id})
            RETURN a, c
            """,
            id=input.assessment_id,
        ).single()
        if not asmt_r:
            raise ValueError(f"Assessment {input.assessment_id} not found")

        assessment = asmt_r["a"]
        course     = asmt_r["c"]

        if course["status"] == "archived":
            raise ValueError("Cannot submit assessment for an archived course")

        if input.marks_obtained > assessment["total_marks"]:
            raise ValueError(
                f"marks_obtained ({input.marks_obtained}) "
                f"exceeds total_marks ({assessment['total_marks']})"
            )

        enroll_r = session.run(
            """
            MATCH (s:Student {id:$sid})-[:HAS_ENROLLMENT]->(e:Enrollment)
                  -[:FOR_COURSE]->(c:Course {id:$cid})
            RETURN e
            """,
            sid=input.student_id, cid=course["id"],
        ).single()
        if not enroll_r:
            raise ValueError("Student is not enrolled in the course for this assessment")
        if enroll_r["e"]["status"] == "dropped":
            raise ValueError("Student has dropped this course")

        dup = session.run(
            """
            MATCH (s:Student {id:$sid})-[:HAS_SUBMISSION]->(sub:Submission)
                  -[:FOR_ASSESSMENT]->(a:Assessment {id:$aid})
            RETURN sub
            """,
            sid=input.student_id, aid=input.assessment_id,
        ).single()
        if dup:
            raise ValueError("Assessment already submitted by this student")

        new_id = next_id(session, "Submission")
        session.run(
            """
            MATCH (s:Student {id:$sid}), (a:Assessment {id:$aid})
            CREATE (s)-[:HAS_SUBMISSION]->(sub:Submission {
                id:             $id,
                marks_obtained: $marks
            })-[:FOR_ASSESSMENT]->(a)
            """,
            sid=input.student_id, aid=input.assessment_id,
            id=new_id, marks=input.marks_obtained,
        )

        recalculate_progress(session, input.student_id, course["id"])

        percentage = round((input.marks_obtained / assessment["total_marks"]) * 100, 2)
        return SubmissionResult(
            submission=Submission(
                id=new_id,
                assessment_id=input.assessment_id,
                student_id=input.student_id,
                marks_obtained=input.marks_obtained,
            ),
            total_marks=assessment["total_marks"],
            marks_obtained=input.marks_obtained,
            percentage=percentage,
        )
