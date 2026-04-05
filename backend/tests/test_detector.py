import os
import sys
from unittest.mock import patch

# Ensure `backend/` is on sys.path so `adaptive_feedback` imports work in tests.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adaptive_feedback.detector import run_detection


@patch("adaptive_feedback.detector.initialize_ai")
def test_empty_code_guard(mock_initialize_ai):
    result = run_detection({"content": "   ", "language": "python", "user_id": "u1", "session_id": "s1"})
    assert result["status"] == "success"
    assert "incomplete_code" in result["error_types"]


@patch("adaptive_feedback.detector.initialize_ai")
@patch("adaptive_feedback.detector.semantic_match")
@patch("adaptive_feedback.detector._judge0_execute")
def test_python_error_uses_semantic_match(mock_judge0_execute, mock_semantic_match, mock_initialize_ai):
    mock_judge0_execute.return_value = {
        "status_id": 7,
        "status_description": "Compilation Error",
        "stdout": "",
        "stderr": "SyntaxError: invalid syntax",
        "is_error": True,
        "raw": {},
    }
    mock_semantic_match.return_value = [
        {"id": "MIS001", "title": "Python is Slow", "score": 0.72, "fix": "Optimize your code."}
    ]

    result = run_detection(
        {"content": "print(123", "language": "python", "user_id": "u1", "session_id": "s1"}
    )
    assert result["error_types"] == ["execution_error"]
    assert result["primary_concept"] == "Python is Slow"
    assert result["diagnosis"][0]["source"] == "semantic_match"
    assert result["semantic_top_match"]["id"] == "MIS001"


@patch("adaptive_feedback.detector.initialize_ai")
@patch("adaptive_feedback.detector.llm_classify")
@patch("adaptive_feedback.detector._judge0_execute")
def test_java_error_uses_llm_hint(mock_judge0_execute, mock_llm_classify, mock_initialize_ai):
    mock_judge0_execute.return_value = {
        "status_id": 7,
        "status_description": "Compilation Error",
        "stdout": "",
        "stderr": "error: cannot find symbol variable x",
        "is_error": True,
        "raw": {},
    }
    mock_llm_classify.return_value = {
        "error_type": "compile_error",
        "explanation": "The variable is undefined in your scope.",
        "fix": "Declare `x` before use.",
        "confidence": 0.81,
    }

    result = run_detection(
        {"content": "System.out.println(x);", "language": "java", "user_id": "u1", "session_id": "s1"}
    )
    assert result["error_types"] == ["compile_error"]
    assert result["diagnosis"][0]["source"] == "llm"
    assert result["diagnosis"][0]["fix"] == "Declare `x` before use."


@patch("adaptive_feedback.detector.initialize_ai")
@patch("adaptive_feedback.detector.semantic_match")
@patch("adaptive_feedback.detector.llm_classify")
@patch("adaptive_feedback.detector._judge0_execute")
def test_success_path_semantic_and_llm(
    mock_judge0_execute, mock_llm_classify, mock_semantic_match, mock_initialize_ai
):
    mock_judge0_execute.return_value = {
        "status_id": 3,
        "status_description": "Accepted",
        "stdout": "ok",
        "stderr": "",
        "is_error": False,
        "raw": {},
    }
    mock_semantic_match.return_value = [
        {"id": "PROB1", "title": "Some Concept", "score": 0.66, "fix": "Do X instead."}
    ]
    mock_llm_classify.return_value = {
        "error_type": "none",
        "explanation": "Executed successfully.",
        "fix": None,
        "confidence": 0.9,
    }

    result = run_detection(
        {"content": "print('ok')", "language": "python", "user_id": "u1", "session_id": "s1"}
    )
    assert result["error_types"] == ["none"]
    assert result["semantic_top_match"]["title"] == "Some Concept"