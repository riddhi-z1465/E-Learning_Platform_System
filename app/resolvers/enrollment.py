from typing import List
from db import get_session, next_id
from app.types import Enrollment, EnrollStudentInput, EnrollmentResult
from app.utils import row_to_enrollment

def get_enrollments() -> List[Enrollment]:
    with get_session() as session:
        rows = session.run(
            """
            MATCH (s:Student)-[:HAS_ENROLLMENT]->(e:Enrollment)-[:FOR_COURSE]->(c:Course)
            RETURN e, s.id AS sid, c.id AS cid
            """
        ).data()
        return [row_to_enrollment({**r["e"], "student_id": r["sid"], "course_id": r["cid"]})
                for r in rows]

def get_student_enrollments(student_id: int) -> List[Enrollment]:
    with get_session() as session:
        rows = session.run(
            """
            MATCH (s:Student {id:$sid})-[:HAS_ENROLLMENT]->(e:Enrollment)-[:FOR_COURSE]->(c:Course)
            RETURN e, s.id AS sid, c.id AS cid
            """,
            sid=student_id,
        ).data()
        return [row_to_enrollment({**r["e"], "student_id": r["sid"], "course_id": r["cid"]})
                for r in rows]

def enroll_student(input: EnrollStudentInput) -> EnrollmentResult:
    """
    Enrolls a student in a course.
    Validations:
        • Student must exist
        • Course must exist and be active (not archived)
        • Student cannot already be enrolled
    """
    with get_session() as session:
        student = session.run(
            "MATCH (s:Student {id:$id}) RETURN s", id=input.student_id
        ).single()
        if not student:
            raise ValueError(f"Student {input.student_id} not found")

        course_r = session.run(
            "MATCH (c:Course {id:$id}) RETURN c", id=input.course_id
        ).single()
        if not course_r:
            raise ValueError(f"Course {input.course_id} not found")
        if course_r["c"]["status"] == "archived":
            raise ValueError("Cannot enroll in an archived course")

        dup = session.run(
            """
            MATCH (s:Student {id:$sid})-[:HAS_ENROLLMENT]->(e:Enrollment)
                  -[:FOR_COURSE]->(c:Course {id:$cid})
            RETURN e
            """,
            sid=input.student_id, cid=input.course_id,
        ).single()
        if dup:
            raise ValueError("Student is already enrolled in this course")

        new_id = next_id(session, "Enrollment")
        session.run(
            """
            MATCH (s:Student {id:$sid}), (c:Course {id:$cid})
            CREATE (s)-[:HAS_ENROLLMENT]->(e:Enrollment {
                id:       $eid,
                progress: 0.0,
                status:   'enrolled'
            })-[:FOR_COURSE]->(c)
            """,
            sid=input.student_id, cid=input.course_id, eid=new_id,
        )
        return EnrollmentResult(
            enrollment=Enrollment(
                id=new_id,
                student_id=input.student_id,
                course_id=input.course_id,
                progress=0.0,
                status="enrolled",
            )
        )

def drop_enrollment(student_id: int, course_id: int) -> Enrollment:
    with get_session() as session:
        r = session.run(
            """
            MATCH (s:Student {id:$sid})-[:HAS_ENROLLMENT]->(e:Enrollment)
                  -[:FOR_COURSE]->(c:Course {id:$cid})
            RETURN e, s.id AS sid, c.id AS cid
            """,
            sid=student_id, cid=course_id,
        ).single()
        if not r:
            raise ValueError("Enrollment not found")
        session.run(
            """
            MATCH (s:Student {id:$sid})-[:HAS_ENROLLMENT]->(e:Enrollment)
                  -[:FOR_COURSE]->(c:Course {id:$cid})
            SET e.status = 'dropped'
            """,
            sid=student_id, cid=course_id,
        )
        return row_to_enrollment({
            **r["e"], "student_id": r["sid"],
            "course_id": r["cid"], "status": "dropped",
        })
