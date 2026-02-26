import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { signup, login } from "../api";
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
    <div className="home">
      <div className="overlay"></div>
      <div className="top-controls">
        <span></span>
        <span></span>
        <span></span>
        <span></span>
      </div>
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
        ← BACK
      </button>

      <div style={{
        position: "relative",
        zIndex: 10,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        color: "white"
      }}>
        <h2 style={{ fontFamily: "Koulen, sans-serif", fontSize: "40px", marginBottom: "20px" }}>
          {loggedUser ? "PROFILE" : (isLogin ? "LOGIN" : "SIGNUP")}
        </h2>

        {loggedUser ? (
          <div style={{ textAlign: "center", background: "rgba(0,0,0,0.5)", padding: "40px", borderRadius: "20px" }}>
            <p style={{ fontSize: "24px", marginBottom: "20px" }}>Welcome, {loggedUser.username}!</p>
            <button
              onClick={handleLogout}
              style={{
                padding: "10px 20px",
                background: "#ff4b2b",
                color: "white",
                border: "none",
                borderRadius: "10px",
                cursor: "pointer",
                fontSize: "18px",
                fontFamily: "Koulen, sans-serif"
              }}
            >
              LOGOUT
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{
            display: "flex",
            flexDirection: "column",
            gap: "15px",
            width: "300px",
            background: "rgba(0,0,0,0.5)",
            padding: "30px",
            borderRadius: "20px"
          }}>
            {error && <p style={{ color: "#ff4b2b", textAlign: "center" }}>{error}</p>}
            {success && <p style={{ color: "#4CAF50", textAlign: "center" }}>{success}</p>}

            <input
              type="text"
              name="username"
              placeholder="Username"
              value={formData.username}
              onChange={handleChange}
              required
              style={{ padding: "12px", borderRadius: "10px", border: "1px solid #999", background: "rgba(255,255,255,0.1)", color: "white" }}
            />

            {!isLogin && (
              <input
                type="email"
                name="email"
                placeholder="Email"
                value={formData.email}
                onChange={handleChange}
                required
                style={{ padding: "12px", borderRadius: "10px", border: "1px solid #999", background: "rgba(255,255,255,0.1)", color: "white" }}
              />
            )}

            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
              style={{ padding: "12px", borderRadius: "10px", border: "1px solid #999", background: "rgba(255,255,255,0.1)", color: "white" }}
            />

            <button type="submit" style={{
              padding: "12px",
              background: "#4CAF50",
              color: "white",
              border: "none",
              borderRadius: "10px",
              cursor: "pointer",
              fontSize: "18px",
              marginTop: "10px",
              fontFamily: "Koulen, sans-serif"
            }}>
              {isLogin ? "LOGIN" : "SIGNUP"}
            </button>

            <p style={{ textAlign: "center", cursor: "pointer", marginTop: "10px", fontSize: "14px" }}
              onClick={() => setIsLogin(!isLogin)}>
              {isLogin ? "Don't have an account? signup" : "Already have an account? Login"}
            </p>
          </form>
        )}
      </div>
    </div>
  );
}