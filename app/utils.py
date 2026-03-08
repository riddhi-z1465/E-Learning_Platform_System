from app.types import Course, Enrollment

def row_to_course(row: dict) -> Course:
    return Course(
        id=row["id"],
        instructor_id=row["instructor_id"],
        title=row["title"],
        description=row.get("description"),
        level=row.get("level"),
        status=row["status"],
    )

def row_to_enrollment(row: dict) -> Enrollment:
    return Enrollment(
        id=row["id"],
        student_id=row["student_id"],
        course_id=row["course_id"],
        progress=row["progress"],
        status=row["status"],
    )

def recalculate_progress(session, student_id: int, course_id: int) -> None:
    """
    Progress = (# assessments submitted by student for this course) /
               (total assessments in course) * 100
    Auto-completes enrollment when progress reaches 100.
    """
    total_res = session.run(
        "MATCH (c:Course {id:$cid})-[:HAS_ASSESSMENT]->(a:Assessment) RETURN count(a) AS total",
        cid=course_id,
    ).single()
    total = total_res["total"] if total_res else 0
    if total == 0:
        return

    submitted_res = session.run(
        """
        MATCH (s:Student {id:$sid})-[:HAS_SUBMISSION]->(sub:Submission)
              -[:FOR_ASSESSMENT]->(a:Assessment)<-[:HAS_ASSESSMENT]-(c:Course {id:$cid})
        RETURN count(sub) AS submitted
        """,
        sid=student_id, cid=course_id,
    ).single()
    submitted = submitted_res["submitted"] if submitted_res else 0

    progress = round((submitted / total) * 100, 2)
    new_status = "completed" if progress >= 100.0 else "enrolled"

    session.run(
        """
        MATCH (s:Student {id:$sid})-[:HAS_ENROLLMENT]->(e:Enrollment)
              -[:FOR_COURSE]->(c:Course {id:$cid})
        SET e.progress = $progress, e.status = $status
        """,
        sid=student_id, cid=course_id,
        progress=progress, status=new_status,
    )
