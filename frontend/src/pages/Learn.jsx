import "../styles/home.css";
import "../styles/learn.css";
import { useNavigate } from "react-router-dom";
import backgroundImage from "../assets/background.png";

import { useState, useEffect } from "react"; // Add useEffect, useState
import { fetchCurriculumCategories, fetchCurriculumProblems } from "../api"; // Assuming these exist in your api.js

export default function Learn() {
  const navigate = useNavigate();
  

  // 1. ADD THIS ARRAY BACK AT THE TOP
  const courses = [
    {
      title: "C++",
      description: "It builds strong programming fundamentals.",
      langParam: "c++",
    },
    {
      title: "JAVA",
      description: "Java teaches disciplined, professional software development.",
      langParam: "java",
    },
    {
      title: "PYTHON",
      description: "Python turns ideas into working solutions quickly.",
      langParam: "python",
    },
  ];
  // 1. Manage the 3-step selection flow
  const [step, setStep] = useState(1); // 1: Lang, 2: Topic, 3: Problem
  const [selectedLang, setSelectedLang] = useState("");
  const [topics, setTopics] = useState([]);
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(false);

  // 2. Fetch Topics when language is picked
  const handleLangSelect = async (lang) => {
    setSelectedLang(lang);
    const cats = await fetchCurriculumCategories(lang);
    setTopics(Array.isArray(cats) ? cats : cats?.topics || []);
    setStep(2);
  };

  // 3. Fetch Problems when topic is picked
  const handleTopicSelect = async (topic) => {
    setLoading(true);
    try {
      const allProbs = await fetchCurriculumProblems();
      
      // 1. Log to console so you can see the data in your browser (F12)
      console.log("Searching for:", selectedLang, "Topic:", topic);
      console.log("All problems from DB:", allProbs);

      // 2. Normalize filter to ignore spaces and capital letters
      const filtered = allProbs.filter(p => {
        const pLang = (p.language || "").trim().toLowerCase();
        const sLang = (selectedLang || "").trim().toLowerCase();
        
        const pTopic = (p.topic || "").trim().toLowerCase();
        const sTopic = (topic || "").trim().toLowerCase();

        return pLang === sLang && pTopic === sTopic;
      });

      setProblems(filtered);
      setStep(3);
    } catch (err) {
      console.error("Error loading problems:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home" style={{ backgroundImage: `url(${backgroundImage})` }}>
      <div className="overlay"></div>
      <h1 className="logo">COUTOR</h1>

      {/* STEP 1: LANGUAGE SELECTION */}
      {step === 1 && (
        <>
          <h2 className="learn-heading">SELECT A LANGUAGE</h2>
          <div className="courses-container">
            {courses.map((course) => (
              <div key={course.title} className="course-card" onClick={() => handleLangSelect(course.langParam)}>
                <h3>{course.title}</h3>
                <p>{course.description}</p>
              </div>
            ))}
          </div>
        </>
      )}

      {/* STEP 2: TOPIC SELECTION */}
      {step === 2 && (
        <>
          <h2 className="learn-heading">CHOOSE A TOPIC ({selectedLang.toUpperCase()})</h2>
          <div className="courses-container">
            {topics.map((topic) => (
              <div key={topic} className="course-card" onClick={() => handleTopicSelect(topic)}>
                <h3>{topic}</h3>
              </div>
            ))}
          </div>
        </>
      )}

      {/* STEP 3: PROBLEM SELECTION */}
      {step === 3 && (
        <>
          <h2 className="learn-heading">PICK A PROBLEM</h2>
          <div className="courses-container">
            {problems.map((p) => (
              <div key={p.id} className="course-card" onClick={() => navigate("/run", { state: { ...p } })}>
                <h3>{p.title}</h3>
                <p>{p.description}</p>
              </div>
            ))}
          </div>
        </>
      )}

      {/* BACK BUTTON LOGIC */}
      <button onClick={() => step > 1 ? setStep(step - 1) : navigate("/")} className="back-btn"> {"<<"} </button>
    </div>
  );
}