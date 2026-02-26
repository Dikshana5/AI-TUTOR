import { useNavigate, useLocation } from "react-router-dom";
import "../styles/BottomNav.css";

export default function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <>
      <div className="nav-bar-bg"></div>

      <nav className="bottom-nav">
        <span
          className={location.pathname === "/" ? "active" : ""}
          onClick={() => navigate("/")}
        >
          HOME
        </span>

        <span
          className={location.pathname === "/learn" ? "active" : ""}
          onClick={() => navigate("/learn")}
        >
          LEARN
        </span>

        <span
          className={location.pathname === "/projects" ? "active" : ""}
          onClick={() => navigate("/projects")}
        >
          PROJECT
        </span>

        <span
          className={location.pathname === "/progress" ? "active" : ""}
          onClick={() => navigate("/progress")}
        >
          PROGRESS
        </span>

        <span
          className={location.pathname === "/account" ? "active" : ""}
          onClick={() => navigate("/account")}
        >
          ACCOUNT
        </span>
      </nav>
    </>
  );
}
