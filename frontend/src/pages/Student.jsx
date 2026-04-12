import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api";

export default function Student() {
  const [tests, setTests] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/student/get_tests").then(res => setTests(res.data)).catch(err => console.error(err));
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <button onClick={() => navigate("/")}>&lt; Back</button>
      <h2>Student Portal - Select a Test</h2>
      <ul style={{listStyle: 'none', padding: 0}}>
        {tests.map(test => (
          <li key={test.id} style={{ margin: "10px 0", border: "1px solid #ddd", padding: "10px" }}>
            <strong>{test.title}</strong>
            <button onClick={() => navigate(`/test/${test.id}`)} style={{ marginLeft: "20px" }}>
              Start Test
            </button>
          </li>
        ))}
      </ul>
      {tests.length === 0 && <p>No tests available.</p>}
    </div>
  );
}