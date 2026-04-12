import { useState } from "react";
import api from "../api/api";
import { useNavigate } from "react-router-dom";

export default function Admin() {
  const navigate = useNavigate();
  const [testTitle, setTestTitle] = useState("");
  const [createdTestId, setCreatedTestId] = useState(null);

  const [question, setQuestion] = useState({
    question: "", option_a: "", option_b: "", option_c: "", option_d: "", correct_answer: ""
  });

  const createTest = async () => {
    try {
      const res = await api.post("/admin/create_test", { title: testTitle });
      setCreatedTestId(res.data.id);
      alert("Test Created with ID: " + res.data.id);
    } catch(err) {
      console.error(err);
      alert("Error creating test");
    }
  };

  const addQuestion = async () => {
    if (!createdTestId) return alert("Create a test first!");
    try {
      await api.post("/admin/add_question", { test_id: createdTestId, ...question });
      alert("Question added!");
      setQuestion({ question: "", option_a: "", option_b: "", option_c: "", option_d: "", correct_answer: "" });
    } catch(err) {
      console.error(err);
      alert("Error adding question");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <button onClick={() => navigate("/")}>&lt; Back</button>
      <h2>Admin Portal</h2>
      
      <div style={{ border: "1px solid #ccc", padding: "10px", marginBottom: "20px" }}>
        <h3>Create Test</h3>
        <input placeholder="Test Title" value={testTitle} onChange={e => setTestTitle(e.target.value)} />
        <button onClick={createTest} style={{ marginLeft: "10px" }}>Create</button>
      </div>

      <div style={{ border: "1px solid #ccc", padding: "10px" }}>
        <h3>Add Question</h3>
        <p>Test ID: {createdTestId || "None"}</p>
        <div style={{display: 'flex', flexDirection: 'column', gap: '10px', maxWidth: '400px'}}>
          <input placeholder="Question" value={question.question} onChange={e => setQuestion({...question, question: e.target.value})} />
          <input placeholder="Option A" value={question.option_a} onChange={e => setQuestion({...question, option_a: e.target.value})} />
          <input placeholder="Option B" value={question.option_b} onChange={e => setQuestion({...question, option_b: e.target.value})} />
          <input placeholder="Option C" value={question.option_c} onChange={e => setQuestion({...question, option_c: e.target.value})} />
          <input placeholder="Option D" value={question.option_d} onChange={e => setQuestion({...question, option_d: e.target.value})} />
          <input placeholder="Correct Answer (e.g. A)" value={question.correct_answer} onChange={e => setQuestion({...question, correct_answer: e.target.value})} />
          <button onClick={addQuestion}>Add Question</button>
        </div>
      </div>
    </div>
  );
}