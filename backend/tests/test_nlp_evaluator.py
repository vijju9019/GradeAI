import pytest
from app.services.nlp_evaluator import nlp_evaluator
from app.models.question import Question, MarkingRubric

def test_empty_answer_evaluation():
    q = Question(
        question_number="1",
        question_text="Explain virtual memory",
        max_marks=10.0,
        model_answer="Virtual memory provides an illusion of large continuous memory using paging.",
    )
    q.required_keywords = ["virtual memory", "paging"]
    
    result = nlp_evaluator.evaluate_answer("", q)
    assert result["suggested_marks"] == 0.0
    assert result["confidence_score"] == 1.0
    assert len(result["missing_keywords"]) == 2
    assert "Student answer is empty or missing" in result["uncertainty_reasons"][0]

def test_full_correct_answer_evaluation():
    q = Question(
        question_number="1",
        question_text="What is a Process and Thread?",
        max_marks=10.0,
        model_answer="A process is an executing program with isolated address space. A thread is a lightweight execution unit inside a process sharing memory.",
    )
    q.required_keywords = ["process", "thread", "address space", "lightweight", "memory"]
    q.important_concepts = ["isolated address space", "lightweight process"]

    student_ans = (
        "A process is a program in execution with an isolated address space. "
        "A thread is a lightweight unit of execution within a process that shares memory and resources with other threads."
    )

    result = nlp_evaluator.evaluate_answer(student_ans, q)
    assert result["suggested_marks"] >= 6.0
    assert result["suggested_marks"] <= 10.0
    assert len(result["matched_keywords"]) >= 4
    assert result["confidence_level"] in ["high", "medium"]

def test_marks_strictly_bounded_by_max_marks():
    q = Question(
        question_number="2",
        question_text="Define binary tree",
        max_marks=5.0,
        model_answer="A binary tree is a hierarchical data structure where each parent node has at most two children called left and right child.",
    )
    q.required_keywords = ["binary tree", "left child", "right child"]

    # Even with redundant extra words, marks should never exceed max_marks (5.0)
    student_ans = q.model_answer + " Perfect answer with exact duplicate text. " + q.model_answer
    result = nlp_evaluator.evaluate_answer(student_ans, q)
    assert result["suggested_marks"] <= 5.0
    assert result["suggested_marks"] >= 0.0

def test_rubric_evaluation_partial_credit():
    q = Question(
        question_number="3",
        question_text="Dijkstra Algorithm",
        max_marks=10.0,
        model_answer="Dijkstra finds shortest path with greedy strategy and min-heap. Edge weights must be non-negative.",
    )
    rubrics = [
        MarkingRubric(criterion_title="Greedy Strategy", allocated_marks=4.0, description="Explains greedy choice"),
        MarkingRubric(criterion_title="Non-Negative Weights", allocated_marks=6.0, description="Mentions non-negative edges")
    ]
    # Student only mentions greedy choice, misses non-negative constraint
    student_ans = "Dijkstra algorithm uses a greedy approach with a priority queue."
    result = nlp_evaluator.evaluate_answer(student_ans, q, rubrics=rubrics)
    assert result["suggested_marks"] < 10.0
    assert len(result["rubric_breakdown"]) == 2
