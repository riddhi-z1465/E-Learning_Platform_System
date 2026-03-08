from typing import List
from db import get_session, next_id
from app.types import Assessment, CreateAssessmentInput

def get_assessments(course_id: int) -> List[Assessment]:
    with get_session() as session:
        rows = session.run(
            "MATCH (c:Course {id:$cid})-[:HAS_ASSESSMENT]->(a:Assessment) RETURN a, c.id AS cid",
            cid=course_id,
        ).data()
        return [Assessment(id=r["a"]["id"], course_id=r["cid"],
                           title=r["a"]["title"], total_marks=r["a"]["total_marks"])
                for r in rows]

def create_assessment(input: CreateAssessmentInput) -> Assessment:
    with get_session() as session:
        course = session.run(
            "MATCH (c:Course {id:$id}) RETURN c", id=input.course_id
        ).single()
        if not course:
            raise ValueError(f"Course {input.course_id} not found")

        new_id = next_id(session, "Assessment")
        session.run(
            """
            MATCH (c:Course {id:$cid})
            CREATE (c)-[:HAS_ASSESSMENT]->(a:Assessment {
                id:          $id,
                title:       $title,
                total_marks: $total_marks
            })
            """,
            cid=input.course_id, id=new_id,
            title=input.title, total_marks=input.total_marks,
        )
        return Assessment(
            id=new_id, course_id=input.course_id,
            title=input.title, total_marks=input.total_marks,
        )
