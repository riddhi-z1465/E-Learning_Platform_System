from typing import Optional, List
from db import get_session, next_id
from app.types import Instructor, CreateInstructorInput
from app.utils import row_to_course

def get_instructors() -> List[Instructor]:
    with get_session() as session:
        rows = session.run(
            """
            MATCH (i:Instructor)
            OPTIONAL MATCH (i)-[:TEACHES]->(c:Course)
            RETURN i, collect(c) AS courses
            """
        ).data()
        result = []
        for r in rows:
            i = r["i"]
            courses = [row_to_course({**c, "instructor_id": i["id"]}) for c in r["courses"]]
            result.append(Instructor(
                id=i["id"], name=i["name"], email=i["email"],
                expertise=i["expertise"], courses=courses,
            ))
        return result

def get_instructor(id: int) -> Optional[Instructor]:
    with get_session() as session:
        r = session.run(
            """
            MATCH (i:Instructor {id:$id})
            OPTIONAL MATCH (i)-[:TEACHES]->(c:Course)
            RETURN i, collect(c) AS courses
            """,
            id=id,
        ).single()
        if not r:
            return None
        i = r["i"]
        courses = [row_to_course({**c, "instructor_id": i["id"]}) for c in r["courses"]]
        return Instructor(
            id=i["id"], name=i["name"], email=i["email"],
            expertise=i["expertise"], courses=courses,
        )

def create_instructor(input: CreateInstructorInput) -> Instructor:
    with get_session() as session:
        existing = session.run(
            "MATCH (i:Instructor {email:$email}) RETURN i", email=input.email
        ).single()
        if existing:
            raise ValueError(f"Instructor with email '{input.email}' already exists")

        new_id = next_id(session, "Instructor")
        session.run(
            """
            CREATE (i:Instructor {id:$id, name:$name, email:$email, expertise:$expertise})
            """,
            id=new_id, name=input.name, email=input.email, expertise=input.expertise,
        )
        return Instructor(
            id=new_id, name=input.name, email=input.email,
            expertise=input.expertise, courses=[],
        )

def delete_instructor(id: int) -> bool:
    with get_session() as session:
        # Check if the instructor exists first
        r = session.run("MATCH (i:Instructor {id:$id}) RETURN i", id=id).single()
        if not r:
            raise ValueError(f"Instructor {id} not found")
        
        # DETACH DELETE removes the instructor node and any relationships (courses taught, etc.)
        session.run("MATCH (i:Instructor {id:$id}) DETACH DELETE i", id=id)
        return True
