from typing import Optional, List
from db import get_session, next_id
from app.types import Student, CreateStudentInput

def get_students() -> List[Student]:
    with get_session() as session:
        rows = session.run("MATCH (s:Student) RETURN s").data()
        return [Student(id=r["s"]["id"], name=r["s"]["name"],
                        email=r["s"]["email"], status=r["s"]["status"]) for r in rows]

def get_student(id: int) -> Optional[Student]:
    with get_session() as session:
        r = session.run("MATCH (s:Student {id:$id}) RETURN s", id=id).single()
        if not r:
            return None
        s = r["s"]
        return Student(id=s["id"], name=s["name"], email=s["email"], status=s["status"])

def create_student(input: CreateStudentInput) -> Student:
    with get_session() as session:
        existing = session.run(
            "MATCH (s:Student {email:$email}) RETURN s", email=input.email
        ).single()
        if existing:
            raise ValueError(f"Student with email '{input.email}' already exists")

        new_id = next_id(session, "Student")
        session.run(
            "CREATE (s:Student {id:$id, name:$name, email:$email, status:'active'})",
            id=new_id, name=input.name, email=input.email,
        )
        return Student(id=new_id, name=input.name, email=input.email, status="active")

def delete_student(id: int) -> bool:
    with get_session() as session:
        # Check if the student exists first
        r = session.run("MATCH (s:Student {id:$id}) RETURN s", id=id).single()
        if not r:
            raise ValueError(f"Student {id} not found")
        
        # DETACH DELETE removes the student node and any relationships (enrollments, submissions, etc.)
        session.run("MATCH (s:Student {id:$id}) DETACH DELETE s", id=id)
        return True
