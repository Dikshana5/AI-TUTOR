import streamlit as st
import os
import sys

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import DetectResponse
from adaptive_feedback.engine import (
    analyze_student_submission,
    get_next_step,
    refresh_vector_brain,
)
from generate_content import generate_problems_for_lang

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Adaptive Tutor", layout="wide")
st.title("🤖 Personal AI Coding Tutor")
st.markdown("---")

# --- SIDEBAR: SETTINGS & TOOLS ---
with st.sidebar:
    st.header("Settings")
    language = st.selectbox("Select Language", ["Python", "Java", "C++", "JavaScript"])
    topic = st.text_input("Current Topic", "Decorators & Generators")
    
    st.divider()
    
    # Tool 1: Manual Load
    if st.button("🎯 Load New Challenge"):
        # We indent this block so Python knows it belongs to the button
        fake_analysis = DetectResponse(
            status="success", 
            error_types=["none"], 
            primary_concept=topic, 
            diagnosis=[], 
            confidence=1.0
        )
        st.session_state.current_problem = get_next_step(fake_analysis, current_lang=language)
        st.rerun()

    # Tool 2: Force Re-index
    if st.button("🔄 Force Re-index Brain"):
        refresh_vector_brain()
        st.success("Brain Updated!")

# --- SESSION STATE ---
if "current_problem" not in st.session_state:
    st.session_state.current_problem = {
        "title": "Welcome! Select a topic to start.",
        "description": "Click 'Load New Challenge' in the sidebar to begin."
    }

# --- MAIN UI: PROBLEM DISPLAY ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Current Task")
    st.info(f"**{st.session_state.current_problem.get('title')}**")
    st.write(st.session_state.current_problem.get('description'))
    
    student_code = st.text_area("Write your code here:", height=300, placeholder="# Enter your solution...")
    
    if st.button("🚀 Submit Solution"):
        if student_code.strip() == "":
            st.warning("Please enter some code first!")
        else:
            with st.spinner("AI is analyzing your logic..."):
                analysis = analyze_student_submission(student_code, language=language)
                next_task = get_next_step(analysis, current_lang=language)
                
                st.session_state.analysis = analysis
                st.session_state.current_problem = next_task
                st.rerun()

# --- MAIN UI: FEEDBACK DISPLAY ---
with col2:
    st.subheader("💡 AI Feedback")
    if "analysis" in st.session_state:
        res = st.session_state.analysis
        st.metric("AI Confidence", f"{res.confidence * 100:.0f}%")
        
        if "none" in res.error_types:
            st.success("✅ Perfect! You've mastered this concept.")
            st.balloons()
        else:
            st.error(f"Detected Issues: {', '.join(res.error_types)}")
            for diag in res.diagnosis:
                st.write(f"**Professor Note:** {diag.get('message', 'Keep trying!')}")
                if diag.get('fix'):
                    with st.expander("See Suggested Fix"):
                        st.code(diag['fix'])
        
        st.divider()
        st.markdown("### 📈 Your Adaptive Path")
        st.write(f"Next task: **{st.session_state.current_problem.get('title')}**")

# --- JIT GENERATION TRIGGER ---
if st.session_state.current_problem.get("id") == "error":
    st.warning("Generating fresh curriculum...")
    with st.spinner("Calling AI Architect..."):
        new_probs = generate_problems_for_lang(language, topic)
        if new_probs:
            st.session_state.current_problem = new_probs[0]
            st.rerun()