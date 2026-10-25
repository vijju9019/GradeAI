import io
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_e2e():
    print("=== STARTING GRADEAI END-TO-END WORKFLOW TEST ===")

    # 1. Login with demo teacher credentials
    print("\n[Step 1] Authenticating teacher...")
    login_res = httpx.post(f"{BASE_URL}/auth/login", json={
        "email": "teacher@gradeai.edu",
        "password": "password123"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    user_name = login_res.json()["user"]["full_name"]
    print(f"-> Authenticated as: {user_name} (Token acquired)")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check system health
    print("\n[Step 2] Checking System Health & AI Models...")
    health_res = httpx.get(f"{BASE_URL}/admin/health")
    assert health_res.status_code == 200
    h = health_res.json()
    print(f"-> Health: {h['status']} | Embedding Model Ready: {h['embedding_model_ready']} ({h['embedding_model_name']}) | Tesseract OCR: {h['tesseract_ocr_available']}")

    # 3. Create Examination
    print("\n[Step 3] Creating new Examination...")
    exam_res = httpx.post(f"{BASE_URL}/examinations", headers=headers, json={
        "title": "SE402: Software Architecture & Patterns",
        "subject": "Software Engineering",
        "class_name": "B.Tech Semester VI",
        "academic_year": "2026-2027",
        "exam_date": "2026-10-25",
        "total_marks": 20.0,
        "duration_minutes": 90,
        "description": "Comprehensive evaluation of design patterns and architectural tiers."
    })
    assert exam_res.status_code == 201, f"Create exam failed: {exam_res.text}"
    exam_id = exam_res.json()["id"]
    print(f"-> Examination created with ID: {exam_id} ('{exam_res.json()['title']}')")

    # 4. Add Question with Model Answer, Keywords & Rubrics
    print("\n[Step 4] Adding Question & Marking Rubric Scheme...")
    q_res = httpx.post(f"{BASE_URL}/examinations/{exam_id}/questions", headers=headers, json={
        "question_number": "1",
        "question_text": "Explain the Model-View-Controller (MVC) architectural pattern and discuss the role of each component.",
        "max_marks": 20.0,
        "model_answer": (
            "The Model-View-Controller (MVC) architectural pattern divides software logic into three interconnected components: "
            "1. Model manages the application data, business logic, and state. "
            "2. View renders the user interface presentation to the client. "
            "3. Controller processes incoming user input, alters the model state, and updates the view accordingly. "
            "This achieves loose coupling, separation of concerns, and parallel development."
        ),
        "required_keywords": ["Model", "View", "Controller", "data", "presentation", "input", "separation of concerns"],
        "important_concepts": ["loose coupling", "business logic", "UI presentation"],
        "rubrics": [
            {
                "criterion_title": "Model Component Definition",
                "allocated_marks": 6.0,
                "description": "Explains data structures, state persistence, and business rules"
            },
            {
                "criterion_title": "View Component Definition",
                "allocated_marks": 6.0,
                "description": "Explains user interface rendering and display logic"
            },
            {
                "criterion_title": "Controller Role & Decoupling",
                "allocated_marks": 8.0,
                "description": "Explains event dispatching, input handling, and loose coupling benefits"
            }
        ]
    })
    assert q_res.status_code == 201, f"Add question failed: {q_res.text}"
    q_id = q_res.json()["id"]
    print(f"-> Question added (ID: {q_id}) with {len(q_res.json()['rubrics'])} rubric criteria.")

    # 5. Create Student Submission & Upload Answer Document
    print("\n[Step 5] Ingesting Student Answer Sheet...")
    sub_res = httpx.post(f"{BASE_URL}/examinations/{exam_id}/submissions", headers=headers, json={
        "examination_id": exam_id,
        "student_id": "STU-2026-888",
        "student_name": "Divya Krishnan",
        "student_roll_no": "CS-22-205"
    })
    assert sub_res.status_code == 201
    sub_id = sub_res.json()["id"]

    # Synthetic student answer content
    student_answer_content = (
        "Examination Answer Sheet\n"
        "Student: Divya Krishnan | ID: STU-2026-888\n\n"
        "Q1: The Model-View-Controller (MVC) pattern promotes separation of concerns by partitioning software into three parts:\n"
        "- Model: Holds the application data, entity models, and business logic.\n"
        "- View: Handles the visual user interface presentation that users interact with.\n"
        "- Controller: Receives HTTP requests or user input, manipulates the Model, and directs which View to render.\n"
        "This architectural separation ensures loose coupling and makes code maintainable."
    )

    files = {"file": ("student_answer_sheet.txt", io.BytesIO(student_answer_content.encode("utf-8")), "text/plain")}
    up_res = httpx.post(f"{BASE_URL}/submissions/{sub_id}/upload", headers=headers, files=files)
    assert up_res.status_code == 201, f"Upload failed: {up_res.text}"
    print(f"-> Answer sheet uploaded and text extracted. Document ID: {up_res.json()['id']}, Pages: {up_res.json()['page_count']}")

    # 6. Run Segmentation
    print("\n[Step 6] Running Answer Segmentation...")
    seg_res = httpx.post(f"{BASE_URL}/submissions/{sub_id}/segment", headers=headers)
    assert seg_res.status_code == 200
    print(f"-> Segmentation complete: {seg_res.json()['mapped_count']} questions mapped.")

    # 7. Run AI/NLP Evaluation Engine
    print("\n[Step 7] Running AI/NLP Evaluation Service...")
    eval_res = httpx.post(f"{BASE_URL}/submissions/{sub_id}/evaluate", headers=headers)
    assert eval_res.status_code == 200
    eval_json = eval_res.json()
    print(f"-> Suggested Marks: {eval_json['total_suggested_marks']} / 20.0 (Status: {eval_json['status']})")

    # Fetch detailed evaluation results
    det_res = httpx.get(f"{BASE_URL}/submissions/{sub_id}/evaluation-results", headers=headers)
    assert det_res.status_code == 200
    item = det_res.json()[0]
    print(f"-> Confidence Level: {item['confidence_level']} (Score: {item['confidence_score']})")
    print(f"-> Matched Keywords: {item['matched_keywords']}")
    print(f"-> Lexical TF-IDF: {item['cosine_similarity_score']} | Semantic Match: {item['semantic_similarity_score']}")

    # 8. Teacher Review & Override
    print("\n[Step 8] Teacher Review Workspace (Editing mark with human oversight)...")
    rev_res = httpx.post(f"{BASE_URL}/reviews/submissions/{sub_id}/override", headers=headers, json={
        "question_id": q_id,
        "teacher_marks": 18.5,
        "review_notes": "Very precise breakdown of Controller request routing and Model state updates. High technical clarity."
    })
    assert rev_res.status_code == 200
    print(f"-> Teacher approved mark: {rev_res.json()['teacher_marks']} (Overridden: {rev_res.json()['is_overridden']})")

    # 9. Finalize Submission
    print("\n[Step 9] Certifying & Finalizing Submission...")
    fin_res = httpx.post(f"{BASE_URL}/reviews/submissions/{sub_id}/finalize", headers=headers)
    assert fin_res.status_code == 200
    fin_data = fin_res.json()
    assert fin_data["is_finalized"] is True
    print(f"-> Finalized Status: {fin_data['status']} | Final Score: {fin_data['total_approved_marks']} / 20.0 ({fin_data['percentage']}%)")

    # 10. Generate PDF Report & Exports
    print("\n[Step 10] Generating Official Scorecard Report...")
    pdf_res = httpx.get(f"{BASE_URL}/reports/submissions/{sub_id}/report/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers.get("content-type") == "application/pdf"
    assert len(pdf_res.content) > 1000
    print(f"-> PDF Scorecard generated: {len(pdf_res.content)} bytes (Starts with {pdf_res.content[:5]})")

    csv_res = httpx.get(f"{BASE_URL}/reports/examinations/{exam_id}/report/csv", headers=headers)
    assert csv_res.status_code == 200
    assert "Divya Krishnan" in csv_res.text
    print(f"-> CSV export verified: Student 'Divya Krishnan' with approved marks found in CSV.")

    print("\n=== ALL 10 END-TO-END WORKFLOW STEPS VERIFIED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_e2e()
