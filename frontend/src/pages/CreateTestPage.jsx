import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api";
import { PlusCircle, Trash2, ArrowLeft, Save } from "lucide-react";
import toast from "react-hot-toast";

export default function CreateTestPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ title: "", duration: 30 });
  const [questions, setQuestions] = useState([
    { question_text: "", option_a: "", option_b: "", option_c: "", option_d: "", correct_answer: "A" }
  ]);

  const handleAddQuestion = () => {
    setQuestions([
      ...questions,
      { question_text: "", option_a: "", option_b: "", option_c: "", option_d: "", correct_answer: "A" }
    ]);
  };

  const handleRemoveQuestion = (idx) => {
    const updated = questions.filter((_, i) => i !== idx);
    setQuestions(updated);
  };

  const handleChangeQuestion = (idx, field, value) => {
    const updated = [...questions];
    updated[idx][field] = value;
    setQuestions(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (questions.length === 0) {
      toast.error("You must add at least one question!");
      return;
    }

    setLoading(true);
    try {
      await api.post("/test/create", {
         title: formData.title,
         duration: parseInt(formData.duration),
         questions: questions
      });
      toast.success("Test Created Successfully!");
      navigate("/admin");
    } catch(err) {
      toast.error("Failed to create test: " + (err.response?.data?.detail?.[0]?.msg || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
       <header className="bg-white shadow py-4 px-8 flex items-center border-b-4 border-primary-500 gap-4">
         <button onClick={() => navigate("/admin")} className="p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition">
             <ArrowLeft className="w-5 h-5 text-gray-700"/>
         </button>
         <h1 className="text-2xl font-bold text-gray-800">Create Custom Test</h1>
       </header>
       
       <main className="flex-1 p-8 max-w-5xl w-full mx-auto">
         <form onSubmit={handleSubmit} className="bg-white p-6 md:p-10 rounded-2xl shadow-sm border border-gray-200">
            {/* Test Metadata */}
            <div className="flex flex-col md:flex-row gap-6 mb-8 pb-8 border-b">
               <div className="flex-1">
                 <label className="block text-sm font-semibold text-gray-700 mb-2">Test Title</label>
                 <input required type="text" placeholder="e.g., Data Structures Midterm" className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary-500 outline-none" 
                   value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} />
               </div>
               <div className="w-48">
                 <label className="block text-sm font-semibold text-gray-700 mb-2">Duration (minutes)</label>
                 <input required type="number" min="1" className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary-500 outline-none" 
                   value={formData.duration} onChange={e => setFormData({...formData, duration: e.target.value})} />
               </div>
            </div>

            {/* Questions Section */}
            <div className="mb-6 flex justify-between items-center">
               <h3 className="text-xl font-bold text-gray-800">Questions ({questions.length})</h3>
               <button type="button" onClick={handleAddQuestion} className="flex items-center gap-2 text-sm font-bold bg-blue-50 text-blue-600 px-4 py-2 rounded-lg hover:bg-blue-100 transition">
                 <PlusCircle className="w-4 h-4"/> Add Question
               </button>
            </div>

            <div className="flex flex-col gap-6 mb-8">
              {questions.map((q, idx) => (
                 <div key={idx} className="p-6 border border-gray-200 rounded-xl bg-gray-50 relative group transition-all animate-fade-in">
                    <div className="flex justify-between items-start mb-4">
                       <span className="font-bold text-gray-700">Question {idx + 1}</span>
                       {questions.length > 1 && (
                         <button type="button" onClick={() => handleRemoveQuestion(idx)} className="text-red-500 bg-red-50 p-2 rounded-lg hover:bg-red-100 transition" title="Remove Question">
                           <Trash2 className="w-4 h-4"/>
                         </button>
                       )}
                    </div>
                    
                    <textarea required placeholder="Enter the question text here..." className="w-full border border-gray-300 rounded-xl px-4 py-3 mb-4 focus:ring-2 focus:ring-primary-500 outline-none resize-none" rows="2"
                       value={q.question_text} onChange={e => handleChangeQuestion(idx, 'question_text', e.target.value)}></textarea>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                       {['A', 'B', 'C', 'D'].map(opt => (
                         <div key={opt} className="flex items-center bg-white border border-gray-200 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-primary-500">
                            <span className="bg-gray-100 px-4 py-3 font-bold text-gray-600 border-r border-gray-200">{opt}</span>
                            <input required type="text" placeholder={`Option ${opt}`} className="w-full px-4 py-3 outline-none" 
                              value={q[`option_${opt.toLowerCase()}`]} onChange={e => handleChangeQuestion(idx, `option_${opt.toLowerCase()}`, e.target.value)} />
                         </div>
                       ))}
                    </div>

                    <div className="flex items-center gap-4">
                       <label className="text-sm font-semibold text-gray-700">Correct Answer:</label>
                       <select className="border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-primary-500 bg-white font-bold"
                          value={q.correct_answer} onChange={e => handleChangeQuestion(idx, 'correct_answer', e.target.value)}>
                          <option value="A">Option A</option>
                          <option value="B">Option B</option>
                          <option value="C">Option C</option>
                          <option value="D">Option D</option>
                       </select>
                    </div>
                 </div>
              ))}
            </div>

            <button type="submit" disabled={loading} className="w-full md:w-auto flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 text-white font-bold py-3 px-8 rounded-xl shadow-lg transition md:ml-auto disabled:opacity-70 disabled:cursor-not-allowed">
              {loading ? <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span> : <><Save className="w-5 h-5"/> Publish Test</>}
            </button>
         </form>
       </main>
    </div>
  );
}