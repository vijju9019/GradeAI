import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.examination import Examination, ExamStatus
from app.models.question import Question, MarkingRubric
from app.models.submission import StudentSubmission, SubmissionStatus
from app.models.document import UploadedDocument, ExtractedPage
from app.models.evaluation import ExtractedAnswer, EvaluationResult, ApprovedMark
from app.services.nlp_evaluator import nlp_evaluator
from app.services.teacher_review import teacher_review_service

def seed():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Users
        teacher = db.query(User).filter(User.email == "teacher@gradeai.edu").first()
        if not teacher:
            teacher = User(
                email="teacher@gradeai.edu",
                full_name="Prof. Sarah Jenkins",
                hashed_password=get_password_hash("password123"),
                role=UserRole.TEACHER.value,
                is_active=True
            )
            db.add(teacher)

        admin = db.query(User).filter(User.email == "admin@gradeai.edu").first()
        if not admin:
            admin = User(
                email="admin@gradeai.edu",
                full_name="Dr. Alan Turing (Admin)",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN.value,
                is_active=True
            )
            db.add(admin)

        db.commit()
        db.refresh(teacher)
        db.refresh(admin)
        print(f"Users seeded: {teacher.email} (Teacher), {admin.email} (Admin)")

        # 2. Seed Examination
        exam = db.query(Examination).filter(Examination.title == "CS301: Data Structures & Operating Systems").first()
        if not exam:
            exam = Examination(
                title="CS301: Data Structures & Operating Systems",
                subject="Computer Science & Engineering",
                class_name="B.Tech Semester V",
                academic_year="2026-2027",
                exam_date="2026-10-25",
                total_marks=50.0,
                duration_minutes=120,
                description="Mid-term comprehensive assessment on core systems and algorithmic principles.",
                status=ExamStatus.READY.value,
                created_by_id=teacher.id
            )
            db.add(exam)
            db.commit()
            db.refresh(exam)
            print(f"Examination created: {exam.title} (ID: {exam.id})")

            # 3. Seed Questions & Rubrics
            q1 = Question(
                examination_id=exam.id,
                question_number="1",
                question_text="Explain the concept of Virtual Memory and how Paging is used to implement it. What is a Page Fault?",
                max_marks=10.0,
                model_answer=(
                    "Virtual memory is a memory management technique that provides an idealized abstraction of the storage "
                    "resources available on a machine, creating the illusion of a very large uniform memory space. "
                    "Paging divides physical memory into fixed-size blocks called frames, and logical memory into blocks called pages. "
                    "The operating system maintains a page table for each process to map logical page numbers to physical frame numbers. "
                    "A page fault occurs when a program attempts to access a memory block mapped in virtual address space but not currently "
                    "loaded into physical RAM. The OS page fault handler retrieves the required page from secondary disk storage into an available RAM frame."
                ),
                order_index=1
            )
            q1.required_keywords = ["virtual memory", "paging", "frame", "page table", "page fault", "RAM", "disk"]
            q1.important_concepts = ["address translation", "swapping", "secondary storage illusion"]
            q1.alternative_answers = [
                "Virtual memory allows execution of processes that may not be completely in memory. Paging maps virtual addresses to physical frames using page tables. An interrupt called a page fault triggers disk read when a page is absent from physical RAM."
            ]
            db.add(q1)
            db.commit()
            db.refresh(q1)

            # Rubrics for Q1
            db.add_all([
                MarkingRubric(question_id=q1.id, criterion_title="Concept of Virtual Memory", description="Explains virtual abstraction and RAM-disk hierarchy", allocated_marks=3.0, order_index=1),
                MarkingRubric(question_id=q1.id, criterion_title="Paging & Page Table Mechanism", description="Details pages, frames, and address mapping", allocated_marks=4.0, order_index=2),
                MarkingRubric(question_id=q1.id, criterion_title="Page Fault Handling", description="Accurate definition of page fault interrupt and disk fetch", allocated_marks=3.0, order_index=3)
            ])

            q2 = Question(
                examination_id=exam.id,
                question_number="2",
                question_text="Compare a Process vs a Thread in an operating system. Discuss the key advantages of multithreading.",
                max_marks=10.0,
                model_answer=(
                    "A process is an executing instance of a computer program that has its own independent address space, memory, "
                    "file descriptors, and security context. A thread is the smallest unit of execution within a process, often called a lightweight process. "
                    "Threads belonging to the same process share the same code segment, data segment, and open files, but maintain their own program counter, "
                    "registers, and stack. "
                    "Key advantages of multithreading include improved responsiveness, efficient resource sharing without expensive inter-process communication, "
                    "lower overhead for context switching, and enhanced throughput on multicore processor architectures."
                ),
                order_index=2
            )
            q2.required_keywords = ["process", "thread", "address space", "context switch", "stack", "multithreading", "responsiveness"]
            q2.important_concepts = ["lightweight process", "shared memory", "multicore utilization"]
            db.add(q2)
            db.commit()
            db.refresh(q2)

            db.add_all([
                MarkingRubric(question_id=q2.id, criterion_title="Process vs Thread Definition", description="Distinction between isolated process and shared threads", allocated_marks=4.0, order_index=1),
                MarkingRubric(question_id=q2.id, criterion_title="Memory & State Sharing", description="Shares code/data/heap, private registers/stack", allocated_marks=3.0, order_index=2),
                MarkingRubric(question_id=q2.id, criterion_title="Advantages of Multithreading", description="Responsiveness, low overhead context switch, concurrency", allocated_marks=3.0, order_index=3)
            ])

            q3 = Question(
                examination_id=exam.id,
                question_number="3",
                question_text="What is a Binary Search Tree (BST)? Explain its insertion and search operations with time complexity analysis. Under what conditions does it degenerate into a linked list?",
                max_marks=15.0,
                model_answer=(
                    "A Binary Search Tree (BST) is a node-based binary tree data structure where each node satisfies the BST ordering invariant: "
                    "the key in any node is strictly greater than all keys in its left subtree, and strictly less than all keys in its right subtree. "
                    "Search operation begins at the root, comparing target key with current node: if equal, search terminates; if smaller, recurse left; if larger, recurse right. "
                    "Insertion follows the same traversal until finding a null reference where the new leaf node is attached. "
                    "For a balanced BST with height h, both search and insertion take O(h) = O(log n) time. "
                    "If keys are inserted in strictly ascending or descending sorted order, the BST degenerates into a linear linked list (skewed tree), causing worst-case height h = n and time complexity O(n)."
                ),
                order_index=3
            )
            q3.required_keywords = ["binary search tree", "BST", "left subtree", "right subtree", "O(log n)", "O(n)", "degenerate", "sorted"]
            q3.important_concepts = ["BST invariant", "tree height", "worst-case skew"]
            db.add(q3)
            db.commit()
            db.refresh(q3)

            db.add_all([
                MarkingRubric(question_id=q3.id, criterion_title="BST Invariant & Definition", description="Clear definition of left < root < right rule", allocated_marks=4.0, order_index=1),
                MarkingRubric(question_id=q3.id, criterion_title="Search & Insertion Algorithms", description="Step-by-step traversal and base cases", allocated_marks=6.0, order_index=2),
                MarkingRubric(question_id=q3.id, criterion_title="Degeneracy & Complexity Analysis", description="Sorted input skew, O(log n) vs O(n)", allocated_marks=5.0, order_index=3)
            ])

            q4 = Question(
                examination_id=exam.id,
                question_number="4",
                question_text="Describe Dijkstra's algorithm for finding the single-source shortest path in a weighted graph. Provide its time complexity when implemented with a min-priority queue.",
                max_marks=15.0,
                model_answer=(
                    "Dijkstra's algorithm is a greedy graph traversal algorithm that finds the shortest path from a starting source vertex "
                    "to all other vertices in a directed or undirected graph with non-negative edge weights. "
                    "It maintains an array of tentative distances (initialized to infinity, source = 0) and a min-priority queue of unvisited vertices. "
                    "In each step, it extracts the unvisited vertex u with minimum tentative distance and relaxes each outgoing edge (u, v): "
                    "if dist[u] + weight(u, v) < dist[v], then dist[v] is updated and the priority queue is refreshed. "
                    "When implemented using a binary min-heap / priority queue with adjacency list representation, each vertex extraction takes O(log V) time, "
                    "and each edge relaxation takes O(log V) time, yielding a total time complexity of O((V + E) log V)."
                ),
                order_index=4
            )
            q4.required_keywords = ["Dijkstra", "shortest path", "greedy", "min-priority queue", "relaxation", "non-negative", "O((V + E) log V)"]
            q4.important_concepts = ["edge relaxation", "greedy choice", "non-negative weight constraint"]
            db.add(q4)
            db.commit()
            db.refresh(q4)

            db.add_all([
                MarkingRubric(question_id=q4.id, criterion_title="Algorithm Core & Greedy Strategy", description="Extract min distance vertex and relax edges", allocated_marks=6.0, order_index=1),
                MarkingRubric(question_id=q4.id, criterion_title="Non-Negative Weight Constraint", description="Explicit note on why negative edges fail", allocated_marks=4.0, order_index=2),
                MarkingRubric(question_id=q4.id, criterion_title="Complexity with Min-Heap", description="Derivation of O((V + E) log V)", allocated_marks=5.0, order_index=3)
            ])
            db.commit()
            print("4 Examination questions and rubrics seeded.")

        # 4. Seed Submissions & Evaluate
        sub1 = db.query(StudentSubmission).filter(StudentSubmission.student_id == "STU-2026-001").first()
        if not sub1:
            sub1 = StudentSubmission(
                examination_id=exam.id,
                student_id="STU-2026-001",
                student_name="Aarav Sharma",
                student_roll_no="CS-22-045",
                status=SubmissionStatus.UPLOADED.value
            )
            db.add(sub1)
            db.commit()
            db.refresh(sub1)

            # Add answers for Aarav (High Quality)
            ans1_1 = ExtractedAnswer(
                submission_id=sub1.id,
                question_id=1,
                raw_answer_text=(
                    "Q1: Virtual memory provides an illusion of a large continuous main memory to processes by abstracting "
                    "physical hardware storage. Paging accomplishes this by dividing logical memory into fixed chunks called pages, "
                    "and physical RAM into equal-sized blocks called frames. The page table maintains the mapping between virtual pages "
                    "and physical frame numbers. A page fault occurs when a referenced page is not present in RAM; the hardware raises an "
                    "interrupt, and the operating system page fault handler retrieves the required page from secondary disk storage into an available frame."
                ),
                corrected_answer_text=(
                    "Q1: Virtual memory provides an illusion of a large continuous main memory to processes by abstracting "
                    "physical hardware storage. Paging accomplishes this by dividing logical memory into fixed chunks called pages, "
                    "and physical RAM into equal-sized blocks called frames. The page table maintains the mapping between virtual pages "
                    "and physical frame numbers. A page fault occurs when a referenced page is not present in RAM; the hardware raises an "
                    "interrupt, and the operating system page fault handler retrieves the required page from secondary disk storage into an available frame."
                ),
                segmentation_confidence=0.98
            )
            ans1_2 = ExtractedAnswer(
                submission_id=sub1.id,
                question_id=2,
                raw_answer_text=(
                    "Q2: A process is a program in execution with isolated memory address space, whereas a thread is a lightweight dispatchable "
                    "unit within a process. Threads share the heap, code, and global data of the parent process, but each thread has its own "
                    "stack and program counter. Multithreading improves responsiveness in interactive apps and allows faster context switching with lower overhead."
                ),
                corrected_answer_text=(
                    "Q2: A process is a program in execution with isolated memory address space, whereas a thread is a lightweight dispatchable "
                    "unit within a process. Threads share the heap, code, and global data of the parent process, but each thread has its own "
                    "stack and program counter. Multithreading improves responsiveness in interactive apps and allows faster context switching with lower overhead."
                ),
                segmentation_confidence=0.98
            )
            ans1_3 = ExtractedAnswer(
                submission_id=sub1.id,
                question_id=3,
                raw_answer_text=(
                    "Q3: A Binary Search Tree is a binary tree where each node's left child has a smaller key and the right child has a larger key. "
                    "Search and insertion compare keys recursively and take O(log n) average time on a balanced tree. "
                    "If elements are inserted in already sorted ascending order, the tree degenerates into a singly linked list with O(n) height and linear complexity."
                ),
                corrected_answer_text=(
                    "Q3: A Binary Search Tree is a binary tree where each node's left child has a smaller key and the right child has a larger key. "
                    "Search and insertion compare keys recursively and take O(log n) average time on a balanced tree. "
                    "If elements are inserted in already sorted ascending order, the tree degenerates into a singly linked list with O(n) height and linear complexity."
                ),
                segmentation_confidence=0.95
            )
            ans1_4 = ExtractedAnswer(
                submission_id=sub1.id,
                question_id=4,
                raw_answer_text=(
                    "Q4: Dijkstra's algorithm finds single-source shortest paths in graphs with non-negative edge weights using a greedy strategy. "
                    "It repeatedly selects the closest unvisited vertex using a min-priority queue and relaxes its adjacent edges. "
                    "Using a binary min-heap priority queue, vertex extractions take O(V log V) and edge relaxations take O(E log V), giving total time O((V + E) log V)."
                ),
                corrected_answer_text=(
                    "Q4: Dijkstra's algorithm finds single-source shortest paths in graphs with non-negative edge weights using a greedy strategy. "
                    "It repeatedly selects the closest unvisited vertex using a min-priority queue and relaxes its adjacent edges. "
                    "Using a binary min-heap priority queue, vertex extractions take O(V log V) and edge relaxations take O(E log V), giving total time O((V + E) log V)."
                ),
                segmentation_confidence=0.95
            )
            db.add_all([ans1_1, ans1_2, ans1_3, ans1_4])
            db.commit()

            # Evaluate Aarav's answers
            for ans in [ans1_1, ans1_2, ans1_3, ans1_4]:
                eval_res = nlp_evaluator.evaluate_answer(
                    student_answer=ans.corrected_answer_text,
                    question=ans.question,
                    rubrics=ans.question.rubrics
                )
                er = EvaluationResult(
                    extracted_answer_id=ans.id,
                    question_id=ans.question_id,
                    suggested_marks=eval_res["suggested_marks"],
                    max_marks=eval_res["max_marks"],
                    confidence_level=eval_res["confidence_level"],
                    confidence_score=eval_res["confidence_score"],
                    keyword_coverage_score=eval_res["keyword_coverage_score"],
                    cosine_similarity_score=eval_res["cosine_similarity_score"],
                    semantic_similarity_score=eval_res["semantic_similarity_score"],
                    rubric_score=eval_res["rubric_score"]
                )
                er.matched_keywords = eval_res["matched_keywords"]
                er.missing_keywords = eval_res["missing_keywords"]
                er.matched_concepts = eval_res["matched_concepts"]
                er.missing_concepts = eval_res["missing_concepts"]
                er.rubric_breakdown = eval_res["rubric_breakdown"]
                er.evidence_snippets = eval_res["evidence_snippets"]
                er.uncertainty_reasons = eval_res["uncertainty_reasons"]
                db.add(er)

            sub1.status = SubmissionStatus.EVALUATED.value
            db.commit()

            # Teacher reviews Aarav
            teacher_review_service.batch_approve_submission(db, sub1.id, teacher.id)
            teacher_review_service.finalize_submission(db, sub1.id, teacher.id)
            print("Submission 1 (Aarav Sharma) evaluated, approved, and finalized.")

        # Sub 2: Neha Patel (Partially Correct, In Review)
        sub2 = db.query(StudentSubmission).filter(StudentSubmission.student_id == "STU-2026-002").first()
        if not sub2:
            sub2 = StudentSubmission(
                examination_id=exam.id,
                student_id="STU-2026-002",
                student_name="Neha Patel",
                student_roll_no="CS-22-078",
                status=SubmissionStatus.UPLOADED.value
            )
            db.add(sub2)
            db.commit()
            db.refresh(sub2)

            ans2_1 = ExtractedAnswer(
                submission_id=sub2.id,
                question_id=1,
                raw_answer_text="Virtual memory uses paging to keep pages in memory frames. Page fault is when a page is missing in RAM.",
                corrected_answer_text="Virtual memory uses paging to keep pages in memory frames. Page fault is when a page is missing in RAM.",
                segmentation_confidence=0.85
            )
            ans2_2 = ExtractedAnswer(
                submission_id=sub2.id,
                question_id=2,
                raw_answer_text="Process is heavy and has its own memory. Threads are inside process and share memory. Multithreading is faster.",
                corrected_answer_text="Process is heavy and has its own memory. Threads are inside process and share memory. Multithreading is faster.",
                segmentation_confidence=0.85
            )
            ans2_3 = ExtractedAnswer(
                submission_id=sub2.id,
                question_id=3,
                raw_answer_text="Binary search tree has smaller elements on left and larger on right. Search takes log n time. If sorted numbers are inserted it becomes like a linked list.",
                corrected_answer_text="Binary search tree has smaller elements on left and larger on right. Search takes log n time. If sorted numbers are inserted it becomes like a linked list.",
                segmentation_confidence=0.90
            )
            ans2_4 = ExtractedAnswer(
                submission_id=sub2.id,
                question_id=4,
                raw_answer_text="Dijkstra algorithm finds shortest paths in a graph using priority queue. Edge weights must not be negative.",
                corrected_answer_text="Dijkstra algorithm finds shortest paths in a graph using priority queue. Edge weights must not be negative.",
                segmentation_confidence=0.88
            )
            db.add_all([ans2_1, ans2_2, ans2_3, ans2_4])
            db.commit()

            for ans in [ans2_1, ans2_2, ans2_3, ans2_4]:
                eval_res = nlp_evaluator.evaluate_answer(
                    student_answer=ans.corrected_answer_text,
                    question=ans.question,
                    rubrics=ans.question.rubrics
                )
                er = EvaluationResult(
                    extracted_answer_id=ans.id,
                    question_id=ans.question_id,
                    suggested_marks=eval_res["suggested_marks"],
                    max_marks=eval_res["max_marks"],
                    confidence_level=eval_res["confidence_level"],
                    confidence_score=eval_res["confidence_score"],
                    keyword_coverage_score=eval_res["keyword_coverage_score"],
                    cosine_similarity_score=eval_res["cosine_similarity_score"],
                    semantic_similarity_score=eval_res["semantic_similarity_score"],
                    rubric_score=eval_res["rubric_score"]
                )
                er.matched_keywords = eval_res["matched_keywords"]
                er.missing_keywords = eval_res["missing_keywords"]
                er.matched_concepts = eval_res["matched_concepts"]
                er.missing_concepts = eval_res["missing_concepts"]
                er.rubric_breakdown = eval_res["rubric_breakdown"]
                er.evidence_snippets = eval_res["evidence_snippets"]
                er.uncertainty_reasons = eval_res["uncertainty_reasons"]
                db.add(er)

            sub2.status = SubmissionStatus.EVALUATED.value
            db.commit()

            # Teacher overrides Q1 with a custom note and approves Q2
            teacher_review_service.override_question_mark(
                db=db,
                submission_id=sub2.id,
                question_id=1,
                teacher_marks=6.5,
                review_notes="Concise and correct core definitions, but omitted detailed address translation steps.",
                reviewer_id=teacher.id
            )
            print("Submission 2 (Neha Patel) evaluated with 1 teacher override and pending finalization.")

        # Sub 3: Rohan Verma (Pending Review, with low confidence indicator)
        sub3 = db.query(StudentSubmission).filter(StudentSubmission.student_id == "STU-2026-003").first()
        if not sub3:
            sub3 = StudentSubmission(
                examination_id=exam.id,
                student_id="STU-2026-003",
                student_name="Rohan Verma",
                student_roll_no="CS-22-102",
                status=SubmissionStatus.UPLOADED.value
            )
            db.add(sub3)
            db.commit()
            db.refresh(sub3)

            ans3_1 = ExtractedAnswer(
                submission_id=sub3.id,
                question_id=1,
                raw_answer_text="Virtual memory is RAM cache.",
                corrected_answer_text="Virtual memory is RAM cache.",
                segmentation_confidence=0.50
            )
            ans3_2 = ExtractedAnswer(
                submission_id=sub3.id,
                question_id=2,
                raw_answer_text="Process and thread both run code concurrently.",
                corrected_answer_text="Process and thread both run code concurrently.",
                segmentation_confidence=0.55
            )
            ans3_3 = ExtractedAnswer(
                submission_id=sub3.id,
                question_id=3,
                raw_answer_text="BST is a tree.",
                corrected_answer_text="BST is a tree.",
                segmentation_confidence=0.40
            )
            ans3_4 = ExtractedAnswer(
                submission_id=sub3.id,
                question_id=4,
                raw_answer_text="",
                corrected_answer_text="",
                segmentation_confidence=0.0,
                is_missing=True
            )
            db.add_all([ans3_1, ans3_2, ans3_3, ans3_4])
            db.commit()

            for ans in [ans3_1, ans3_2, ans3_3, ans3_4]:
                eval_res = nlp_evaluator.evaluate_answer(
                    student_answer=ans.corrected_answer_text,
                    question=ans.question,
                    rubrics=ans.question.rubrics
                )
                er = EvaluationResult(
                    extracted_answer_id=ans.id,
                    question_id=ans.question_id,
                    suggested_marks=eval_res["suggested_marks"],
                    max_marks=eval_res["max_marks"],
                    confidence_level=eval_res["confidence_level"],
                    confidence_score=eval_res["confidence_score"],
                    keyword_coverage_score=eval_res["keyword_coverage_score"],
                    cosine_similarity_score=eval_res["cosine_similarity_score"],
                    semantic_similarity_score=eval_res["semantic_similarity_score"],
                    rubric_score=eval_res["rubric_score"]
                )
                er.matched_keywords = eval_res["matched_keywords"]
                er.missing_keywords = eval_res["missing_keywords"]
                er.matched_concepts = eval_res["matched_concepts"]
                er.missing_concepts = eval_res["missing_concepts"]
                er.rubric_breakdown = eval_res["rubric_breakdown"]
                er.evidence_snippets = eval_res["evidence_snippets"]
                er.uncertainty_reasons = eval_res["uncertainty_reasons"]
                db.add(er)

            sub3.status = SubmissionStatus.EVALUATED.value
            db.commit()
            print("Submission 3 (Rohan Verma) evaluated with low confidence warnings for teacher inspection.")

        print("Seed script completed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed()
