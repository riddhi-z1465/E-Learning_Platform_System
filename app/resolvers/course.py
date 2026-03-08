from typing import Optional, List
from db import get_session, next_id
from app.types import Course, CreateCourseInput
from app.utils import row_to_course

def get_courses() -> List[Course]:
    with get_session() as session:
        rows = session.run(
            "MATCH (i:Instructor)-[:TEACHES]->(c:Course) RETURN c, i.id AS iid"
        ).data()
        return [row_to_course({**r["c"], "instructor_id": r["iid"]}) for r in rows]

def get_course(id: int) -> Optional[Course]:
    with get_session() as session:
        r = session.run(
            "MATCH (i:Instructor)-[:TEACHES]->(c:Course {id:$id}) RETURN c, i.id AS iid",
            id=id,
        ).single()
        if not r:
            return None
        return row_to_course({**r["c"], "instructor_id": r["iid"]})

def create_course(input: CreateCourseInput) -> Course:
    with get_session() as session:
        instr = session.run(
            "MATCH (i:Instructor {id:$id}) RETURN i", id=input.instructor_id
        ).single()
        if not instr:
            raise ValueError(f"Instructor {input.instructor_id} not found")

        new_id = next_id(session, "Course")
        session.run(
            """
            MATCH (i:Instructor {id:$iid})
            CREATE (i)-[:TEACHES]->(c:Course {
                id:          $id,
                title:       $title,
                description: $desc,
                level:       $level,
                status:      'active'
            })
            """,
            iid=input.instructor_id, id=new_id,
            title=input.title,
            desc=input.description or "",
            level=input.level or "",
        )
        return Course(
            id=new_id, instructor_id=input.instructor_id,
            title=input.title, description=input.description,
            level=input.level, status="active",
        )

def archive_course(course_id: int) -> Course:
    with get_session() as session:
        r = session.run(
            "MATCH (i:Instructor)-[:TEACHES]->(c:Course {id:$id}) RETURN c, i.id AS iid",
            id=course_id,
        ).single()
        if not r:
            raise ValueError(f"Course {course_id} not found")
        session.run(
            "MATCH (c:Course {id:$id}) SET c.status = 'archived'",
            id=course_id,
        )
        return row_to_course({**r["c"], "instructor_id": r["iid"], "status": "archived"})
