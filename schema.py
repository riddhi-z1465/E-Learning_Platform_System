"""
schema.py – Strawberry GraphQL schema backed by Neo4j Aura.

All database operations use Cypher queries via the neo4j Python driver
and are modularized in the `app/` package.
"""
from typing import Optional, List
import strawberry

# Import types
from app.types import (
    Instructor, Student, Course, Enrollment, Assessment, Submission,
    EnrollmentResult, SubmissionResult, Certificate,
    CreateInstructorInput, CreateStudentInput, CreateCourseInput,
    EnrollStudentInput, CreateAssessmentInput, SubmitAssessmentInput
)

# Import resolvers
from app.resolvers import (
    get_instructors, get_instructor, create_instructor,
    get_students, get_student, create_student,
    get_courses, get_course, create_course, archive_course,
    get_enrollments, get_student_enrollments, enroll_student, drop_enrollment,
    get_assessments, create_assessment,
    get_submissions, get_completion_certificate, submit_assessment
)


# ─── Queries ─────────────────────────────────────────────────────────────────

@strawberry.type
class Query:
    instructors: List[Instructor] = strawberry.field(resolver=get_instructors)
    instructor: Optional[Instructor] = strawberry.field(resolver=get_instructor)
    
    students: List[Student] = strawberry.field(resolver=get_students)
    student: Optional[Student] = strawberry.field(resolver=get_student)
    
    courses: List[Course] = strawberry.field(resolver=get_courses)
    course: Optional[Course] = strawberry.field(resolver=get_course)
    
    enrollments: List[Enrollment] = strawberry.field(resolver=get_enrollments)
    student_enrollments: List[Enrollment] = strawberry.field(resolver=get_student_enrollments)
    
    assessments: List[Assessment] = strawberry.field(resolver=get_assessments)
    submissions: List[Submission] = strawberry.field(resolver=get_submissions)
    
    completion_certificate: Certificate = strawberry.field(resolver=get_completion_certificate)


# ─── Mutations ───────────────────────────────────────────────────────────────

@strawberry.type
class Mutation:
    create_instructor: Instructor = strawberry.mutation(resolver=create_instructor)
    create_student: Student = strawberry.mutation(resolver=create_student)
    
    create_course: Course = strawberry.mutation(resolver=create_course)
    archive_course: Course = strawberry.mutation(resolver=archive_course)
    
    enroll_student: EnrollmentResult = strawberry.mutation(resolver=enroll_student)
    drop_enrollment: Enrollment = strawberry.mutation(resolver=drop_enrollment)
    
    create_assessment: Assessment = strawberry.mutation(resolver=create_assessment)
    submit_assessment: SubmissionResult = strawberry.mutation(resolver=submit_assessment)


# ─── Schema ──────────────────────────────────────────────────────────────────

schema = strawberry.Schema(query=Query, mutation=Mutation)