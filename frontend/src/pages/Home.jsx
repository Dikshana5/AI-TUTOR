import "../styles/home.css";
import { useNavigate } from "react-router-dom";
import backgroundImage from "../assets/background.png";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="home" style={{ backgroundImage: `url(${backgroundImage})` }}>
      {/* dark overlay */}
      <div className="overlay"></div>

      <h1 className="logo">COUTOR</h1>

      <p className="subtitle">
        AN AI-POWERED CODING ASSISTANT DESIGNED TO HELP YOU UNDERSTAND,
        IMPROVE, AND CONFIDENTLY BUILD BETTER SOFTWARE
      </p>


      <div className="button-group">
        <button className="start-btn" onClick={() => navigate("/learn")}>
          START LEARNING
        </button>
      </div>

     
  </div>
  );
}
