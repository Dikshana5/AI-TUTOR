import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home.jsx";
import Learn from "./pages/Learn.jsx";
import Projects from "./pages/Projects.jsx";
import Progress from "./pages/Progress.jsx";
import Account from "./pages/Account.jsx";
import Run from "./pages/Run.jsx";
import BottomNav from "./pages/BottomNav";


export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/learn" element={<Learn />} />
        <Route path="/run" element={<Run />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/account" element={<Account />} />
        <Route
          path="*"
          element={<div style={{ color: "white", padding: "40px" }}>404 - Route Not Found</div>}
        />
      </Routes>
      <BottomNav />
    </BrowserRouter>
  );
}

