import "../styles/home.css";
import "../styles/learn.css";
import { useNavigate } from "react-router-dom";
import backgroundImage from "../assets/background.png";

export default function Learn() {
  const navigate = useNavigate();

  const courses = [
    {
      title: "C++",
      description: "It builds strong programming fundamentals.",
    },
    {
      title: "JAVA",
      description: "Java teaches disciplined, professional software development.",
    },
    {
      title: "PYTHON",
      description: "Python turns ideas into working solutions quickly.",
    },
  ];

  return (
    <div className="home" style={{ backgroundImage: `url(${backgroundImage})` }}>
      {/* dark overlay */}
      <div className="overlay"></div>

      <h1 className="logo">COUTOR</h1>

      <p className="learn-tagline">{'{ CODING YOUR WAY TO LEARNING };'}</p>

      <h2 className="learn-heading">BEGIN YOUR LEARNING JOURNEY!?!!</h2>

      <div className="courses-container">
        {courses.map((course) => (
          <div 
            key={course.title} 
            className="course-card"
            onClick={() => navigate("/run", { state: { language: course.title } })}
            style={{ cursor: "pointer" }}
          >
            <h3>{course.title}</h3>
            <p>{course.description}</p>
          </div>
        ))}
      </div>

      <button 
        onClick={() => navigate("/")}
        style={{
          position: "absolute",
          top: "20px",
          left: "20px",
          padding: "8px 16px",
          background: "#d9d9d9",
          border: "1px solid #999",
          borderRadius: "20px",
          cursor: "pointer",
          fontSize: "16px",
          fontFamily: "Koulen, sans-serif",
          zIndex: 100
        }}
      >
        {"<<"}
      </button>

      
    </div>
  );
}