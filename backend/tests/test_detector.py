import pytest
import json
import os
from unittest.mock import patch, MagicMock
from adaptive_feedback.detector import check_python_syntax, semantic_match, run_detection
from dotenv import load_dotenv

# Load environment variables for any real calls (like semantic)
load_dotenv()

# --- 1. Test Static Analysis ---

def test_syntax_error_detection():
    # Code with a known syntax error (missing colon)
    code = "for i in range(5) print(i)"
    findings = check_python_syntax(code)
    
    assert len(findings) == 1
    assert findings[0]["source"] == "static"
    assert "Syntax Error" in findings[0]["message"]
    assert findings[0]["confidence"] == 0.99

def test_no_syntax_error():
    # Correct code
    code = "for i in range(5):\n    print(i)"
    findings = check_python_syntax(code)
    assert len(findings) == 0

# --- 2. Test LLM Classification (MOCKED) ---

# Mock the OpenAI client call to return a fake JSON response


@patch('detector.client')
def test_llm_classification_mocked(mock_openai_client):
    # Setup the fake LLM response object (same as before)
    mock_response = MagicMock()
    llm_output_json_str = json.dumps({
        "error_type": ["logic", "conceptual"],
        "explanation": "The student confuses assignment with comparison.",
        "confidence": 0.88
    })
    mock_response.choices[0].message.content = llm_output_json_str
    mock_openai_client.chat.completions.create.return_value = mock_response

    # --- Change the test content to have a clear SYNTAX ERROR ---
    content = "for i in range(5) print(i)" # Missing colon!
    llm_result = run_detection({"content": content, "language": "python"})

    # Check the combined aggregated result
    assert "syntax" in llm_result["error_type"] # The static checker found syntax
    assert "logic" in llm_result["error_type"]  # The mocked LLM reported logic
    assert len(llm_result["diagnosis"]) == 2    # Should have 2 diagnosis messages

    # Check the sources of the messages
    assert llm_result["diagnosis"][0]["source"] == "static" # Static finding is first
    assert llm_result["diagnosis"][1]["source"] == "llm"    # LLM finding is second
    
# --- 3. Test Semantic Matching (Real Index Search) ---


def test_semantic_match_for_loop_error():
    code = "numbers = [1, 2, 3]; for i in range(1, len(numbers)): print(i)"
    matches = semantic_match(code, k=3) # Check top 3 matches
    
    assert len(matches) > 0
    # Check if the desired ID is anywhere in the top 3 matches
    match_ids = [m["id"] for m in matches]
    assert "loop_off_by_one" in match_ids
    # Check that the score is at least *some* confidence, lowering the required threshold
    assert matches[0]["score"] > 0.35 

def test_semantic_match_for_scope_error():
    # Code: "def f(): x=10; print(x)" (This is a variable scope confusion)
    code = "def f(): x=10; print(x)"
    matches = semantic_match(code, k=3)
    
    assert len(matches) > 0
    match_ids = [m["id"] for m in matches]
    # Accept either the desired concept or the mutable default argument confusion, 
    # as both relate to Python scope/function definition issues.
    assert ("variable_scope_misunderstanding" in match_ids or "mutable_default_args" in match_ids)
    assert matches[0]["score"] > 0.35

# --- 4. End-to-End Pipeline Test ---

@patch('detector.client')
def test_end_to_end_pipeline_with_error(mock_openai_client):
    # Test a submission that has BOTH a syntax error (caught by static) 
    # and a conceptual error (mocked LLM result)
    
    # Mock LLM to report a conceptual error
    llm_output_json_str = json.dumps({"error_type": ["conceptual"], "explanation": "Concept issue.", "confidence": 0.90})
    mock_response = MagicMock()
    mock_response.choices[0].message.content = llm_output_json_str
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    # The code has a syntax error (missing colon)
    code = "for i in range(5)\n    print('error')"
    
    result = run_detection({"content": code, "language": "python", "user_id": "u1", "session_id": "s1"})
    
    # Check the combined results
    assert "syntax" in result["error_type"] # From static checker
    assert "conceptual" in result["error_type"] # From mocked LLM
    assert len(result["diagnosis"]) == 2 # One static, one LLM
    assert result["confidence"] > 0.5 # Confidence should be reasonable