from app.resolvers.instructor import get_instructors, get_instructor, create_instructor
from app.resolvers.student import get_students, get_student, create_student
from app.resolvers.course import get_courses, get_course, create_course, archive_course
from app.resolvers.enrollment import get_enrollments, get_student_enrollments, enroll_student, drop_enrollment
from app.resolvers.assessment import get_assessments, create_assessment
from app.resolvers.submission import get_submissions, get_completion_certificate, submit_assessment

__all__ = [
    "get_instructors", "get_instructor", "create_instructor",
    "get_students", "get_student", "create_student",
    "get_courses", "get_course", "create_course", "archive_course",
    "get_enrollments", "get_student_enrollments", "enroll_student", "drop_enrollment",
    "get_assessments", "create_assessment",
    "get_submissions", "get_completion_certificate", "submit_assessment",
]
