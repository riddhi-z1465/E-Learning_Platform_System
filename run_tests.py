import requests

API_URL = "http://localhost:8000/graphql"

def run_query(query: str):
    response = requests.post(API_URL, json={"query": query})
    return response.json()

def test_suite():
    print("--- Starting Test Suite ---")
    
    # Setup test data
    create_inst_res = run_query("""
    mutation {
      createInstructor(input: {name: "Test Setup Inst", email: "inst@test.com", expertise: "Test"}) { id }
    }
    """)
    assert "errors" not in create_inst_res or "already exists" in str(create_inst_res)
    inst_q = run_query("""query { instructors { id email } }""")
    inst_id = [i["id"] for i in inst_q["data"]["instructors"] if i["email"] == "inst@test.com"][0]
    
    create_stud_res = run_query("""
    mutation {
      createStudent(input: {name: "Test Setup Stud", email: "stud@test.com"}) { id }
    }
    """)
    assert "errors" not in create_stud_res or "already exists" in str(create_stud_res)
    stud_q = run_query("""query { students { id email } }""")
    stud_id = [s["id"] for s in stud_q["data"]["students"] if s["email"] == "stud@test.com"][0]
    
    # 5. Instructor-course linkage
    print("Test 5: Instructor-course linkage")
    course_res = run_query(f"""
    mutation {{
      createCourse(input: {{instructorId: {inst_id}, title: "Test Linkage Course", level: "Beginner"}}) {{ id title instructorId }}
    }}
    """)
    assert "errors" not in course_res, f"Failed to create course: {course_res}"
    course_id = course_res["data"]["createCourse"]["id"]
    course_check = run_query(f"query {{ course(id: {course_id}) {{ instructorId }} }}")
    assert course_check["data"]["course"]["instructorId"] == inst_id
    print("  ✓ Linkage successful\n")
    
    # 1. Enrollment validation
    print("Test 1: Enrollment validation")
    enroll_1 = run_query(f"""
    mutation {{ enrollStudent(input: {{studentId: {stud_id}, courseId: {course_id}}}) {{ enrollment {{ id }} }} }}
    """)
    assert "errors" not in enroll_1, f"Failed initial enrollment: {enroll_1}"
    
    enroll_dup = run_query(f"""
    mutation {{ enrollStudent(input: {{studentId: {stud_id}, courseId: {course_id}}}) {{ enrollment {{ id }} }} }}
    """)
    assert "errors" in enroll_dup and "already enrolled" in enroll_dup["errors"][0]["message"]
    print("  ✓ Validation prevents duplicate enrollments\n")
    
    # Set up Assessment
    asmt_res = run_query(f"""
    mutation {{ createAssessment(input: {{courseId: {course_id}, title: "Test Asmt 1", totalMarks: 100}}) {{ id }} }}
    """)
    assert "errors" not in asmt_res
    asmt_id = asmt_res["data"]["createAssessment"]["id"]
    
    # 3. Marks calculation
    print("Test 3: Marks calculation")
    submit_invalid = run_query(f"""
    mutation {{ submitAssessment(input: {{assessmentId: {asmt_id}, studentId: {stud_id}, marksObtained: 150}}) {{ percentage }} }}
    """)
    assert "errors" in submit_invalid and "exceeds total_marks" in submit_invalid["errors"][0]["message"]
    print("  ✓ Marks computation boundaries respected\n")
    
    submit_valid = run_query(f"""
    mutation {{ submitAssessment(input: {{assessmentId: {asmt_id}, studentId: {stud_id}, marksObtained: 85.5}}) {{ percentage }} }}
    """)
    assert "errors" not in submit_valid
    assert submit_valid["data"]["submitAssessment"]["percentage"] == 85.5
    print("  ✓ Marks calculation behaves accurately\n")
    
    # 2. Progress tracking & 6. Completion certificate logic
    print("Test 2 & 6: Progress Tracking & Certificate Logic")
    enroll_check = run_query(f"""
    query {{ studentEnrollments(studentId: {stud_id}) {{ courseId progress status }} }}
    """)
    our_enroll = [e for e in enroll_check["data"]["studentEnrollments"] if e["courseId"] == course_id][0]
    assert our_enroll["progress"] == 100.0
    assert our_enroll["status"] == "completed"
    print("  ✓ Progress properly tracks to 100%\n")
    
    cert_res = run_query(f"""
    query {{ completionCertificate(studentId: {stud_id}, courseId: {course_id}) {{ isEligible totalScore maxScore percentage }} }}
    """)
    assert cert_res["data"]["completionCertificate"]["isEligible"] == True
    print("  ✓ Certificate correctly granted for completed course\n")
    
    # 4. Course archive restriction
    print("Test 4: Course archive restriction")
    archive_res = run_query(f"mutation {{ archiveCourse(courseId: {course_id}) {{ status }} }}")
    assert archive_res["data"]["archiveCourse"]["status"] == "archived"
    
    enroll_arch = run_query(f"""
    mutation {{ enrollStudent(input: {{studentId: 1, courseId: {course_id}}}) {{ enrollment {{ id }} }} }}
    """)
    assert "errors" in enroll_arch and "archived course" in enroll_arch["errors"][0]["message"]
    print("  ✓ Archive properly restricts operations\n")
    
    print("--- ALL EXPECTED TESTS PASSED ---")

if __name__ == "__main__":
    test_suite()
