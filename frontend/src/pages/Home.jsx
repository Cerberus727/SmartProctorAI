import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h1>Exam Proctoring System</h1>
      <button onClick={() => navigate("/admin")} style={{ margin: "10px", padding: "10px 20px" }}>
        Admin Portal
      </button>
      <button onClick={() => navigate("/student")} style={{ margin: "10px", padding: "10px 20px" }}>
        Student Portal
      </button>
    </div>
  );
}