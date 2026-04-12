import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import AdminDashboard from "./pages/AdminDashboard";
import StudentDashboard from "./pages/StudentDashboard";
import TestPage from "./pages/TestPage";
import VerificationPage from "./pages/VerificationPage";
import MonitorPage from "./pages/MonitorPage";
import CreateTestPage from "./pages/CreateTestPage";

function App() {
  return (
    <Router>
      <Toaster position="top-right" reverseOrder={false} />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/create-test" element={<CreateTestPage />} />
        <Route path="/student" element={<StudentDashboard />} />
        <Route path="/verify/:testId" element={<VerificationPage />} />
        <Route path="/test/:testId" element={<TestPage />} />
        <Route path="/monitor" element={<MonitorPage />} />
      </Routes>
    </Router>
  );
}

export default App;
