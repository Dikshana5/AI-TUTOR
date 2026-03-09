import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { signup, login } from "../api";
import backgroundImage from "../assets/background.png";
import "../styles/home.css";

export default function Account() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loggedUser, setLoggedUser] = useState(null);

  useEffect(() => {
    const user = localStorage.getItem("user");
    if (user) {
      setLoggedUser(JSON.parse(user));
    }
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    try {
      if (isLogin) {
        const res = await login({
          username: formData.username,
          password: formData.password,
        });
        localStorage.setItem("token", res.access_token);
        localStorage.setItem("user", JSON.stringify({ username: formData.username }));
        setLoggedUser({ username: formData.username });
        setSuccess("Login successful!");
      } else {
        await signup({
          username: formData.username,
          email: formData.email,
          password: formData.password,
        });
        setSuccess("Signup successful! You can now login.");
        setIsLogin(true);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setLoggedUser(null);
  };

  return (
    <div className="home account-page" style={{ backgroundImage: `url(${backgroundImage})` }}>
      <div className="overlay"></div>
      <h1 className="logo">COUTOR</h1>

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

      {/* content container matches other pages alignments */}
      <div className="account-container">
        <h2 className="account-heading">
          {loggedUser ? "PROFILE" : (isLogin ? "LOGIN" : "SIGNUP")}
        </h2>

        {loggedUser ? (
          <div className="auth-box">
            <p className="auth-welcome">Welcome, {loggedUser.username}!</p>
            <div className="user-details">
              <h3>User Details</h3>
              <p><strong>Username:</strong> {loggedUser.username}</p>
              <p><strong>Email:</strong> {loggedUser.email || 'Not provided'}</p>
              <p><strong>Account Created:</strong> March 2026</p>
              <p><strong>Lessons Completed:</strong> 5</p>
            </div>
            <button
              onClick={handleLogout}
              className="auth-logout-btn"
            >
              LOGOUT
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="auth-form">
            {error && <p className="auth-error">{error}</p>}
            {success && <p className="auth-success">{success}</p>}

            <input
              type="text"
              name="username"
              placeholder="Username"
              value={formData.username}
              onChange={handleChange}
              required
              className="auth-input"
            />

            {!isLogin && (
              <input
                type="email"
                name="email"
                placeholder="Email"
                value={formData.email}
                onChange={handleChange}
                required
                className="auth-input"
              />
            )}

            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
              className="auth-input"
            />

            <button type="submit" className="auth-submit-btn">
              {isLogin ? "LOGIN" : "SIGNUP"}
            </button>

            <p className="auth-toggle" onClick={() => setIsLogin(!isLogin)}>
              {isLogin ? "Don't have an account? signup" : "Already have an account? Login"}
            </p>
          </form>
        )}
      </div>
    </div>
  );
}