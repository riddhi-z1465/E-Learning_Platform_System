from typing import Optional, List
import strawberry

# ─── Types ───────────────────────────────────────────────────────────────────

@strawberry.type
class Instructor:
    id:        int
    name:      str
    email:     str
    expertise: str
    courses:   List["Course"]


@strawberry.type
class Student:
    id:     int
    name:   str
    email:  str
    status: str


@strawberry.type
class Course:
    id:            int
    instructor_id: int
    title:         str
    description:   Optional[str]
    level:         Optional[str]
    status:        str


@strawberry.type
class Enrollment:
    id:         int
    student_id: int
    course_id:  int
    progress:   float
    status:     str


@strawberry.type
class Assessment:
    id:          int
    course_id:   int
    title:       str
    total_marks: int


@strawberry.type
class Submission:
    id:             int
    assessment_id:  int
    student_id:     int
    marks_obtained: float


@strawberry.type
class EnrollmentResult:
    enrollment: Enrollment


@strawberry.type
class SubmissionResult:
    submission:     Submission
    total_marks:    int
    marks_obtained: float
    percentage:     float


@strawberry.type
class Certificate:
    student_name:  str
    course_title:  str
    total_score:   float
    max_score:     float
    percentage:    float
    is_eligible:   bool


# ─── Inputs ──────────────────────────────────────────────────────────────────

@strawberry.input
class CreateInstructorInput:
    name:      str
    email:     str
    expertise: str


@strawberry.input
class CreateStudentInput:
    name:  str
    email: str


@strawberry.input
class CreateCourseInput:
    instructor_id: int
    title:         str
    description:   Optional[str] = None
    level:         Optional[str] = None


@strawberry.input
class EnrollStudentInput:
    student_id: int
    course_id:  int


@strawberry.input
class CreateAssessmentInput:
    course_id:   int
    title:       str
    total_marks: int


@strawberry.input
class SubmitAssessmentInput:
    assessment_id:  int
    student_id:     int
    marks_obtained: float
