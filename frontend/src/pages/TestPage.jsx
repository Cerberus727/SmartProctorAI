import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/api";
import { AlertCircle, Clock } from "lucide-react";
import toast from "react-hot-toast";

export default function TestPage() {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const streamIdx = useRef(Math.random());
  const [timeLeft, setTimeLeft] = useState(3600);
  let violationsCount = useRef(0);
  const [streamActive, setStreamActive] = useState(true);

  const submitTest = async () => {
    try {
      const answersArray = Object.keys(answers).map(q_id => ({
          question_id: parseInt(q_id),
          selected_answer: answers[q_id]
      }));
      await api.post("/test/submit", { test_id: parseInt(testId), score: 100, answers: answersArray });
      toast.success("Test Completed Successfully!");
      navigate("/student");
    } catch(err) {
      toast.error("Error submitting test");
    }
  };

  const stopCamera = () => {
    setStreamActive(false);
    try {
      navigator.sendBeacon("http://localhost:8000/api/proctor/stop");
    } catch (err) {}
    api.post("/proctor/stop").catch(() => {});
  };

  const checkViolations = () => {
     if (violationsCount.current >= 5) {
         toast.error("Maximum violations reached. Auto-submitting exam.", {duration: 5000});
         submitTest();
     }
  };

  useEffect(() => {
    setStreamActive(true);
    const timer = setInterval(() => {
      setTimeLeft(prev => { 
         if (prev <= 1) { clearInterval(timer); submitTest(); return 0; }
        return prev - 1;
      });
    }, 1000);

    const handleContext = (e) => { e.preventDefault(); toast.error("Right click is disabled."); };
    
    const handleVisibility = () => {
      if(document.hidden) {
         violationsCount.current += 1;
         api.post("/proctor/log_violation", { test_id: parseInt(testId), event_type: "TAB_SWITCH" }).catch(() => {});
         toast.error("⚠️ WARNING: Tab switch detected! Event logged.");
         checkViolations();
      }
    };

    const handleViolationEvent = (e) => {
        violationsCount.current += 1;
        checkViolations();
    };

    const handleBeforeUnload = () => { stopCamera(); };

    document.addEventListener("contextmenu", handleContext);
    document.addEventListener("visibilitychange", handleVisibility);
    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("violation_detected", handleViolationEvent);

    api.get(`/test/${testId}/questions`).then(res => {
        if(res.data.success) setQuestions(res.data.data);
    }).catch(err => console.error(err));
    api.post("/proctor/start").catch(err => {
      console.log("Proctor start error", err);
    });

    return () => {
      clearInterval(timer);
      document.removeEventListener("contextmenu", handleContext);
      document.removeEventListener("visibilitychange", handleVisibility);
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("violation_detected", handleViolationEvent);
      stopCamera();
    };
  }, [testId]);

  const formatTime = (seconds) => {
      const m = Math.floor(seconds / 60).toString().padStart(2, '0');
      const s = (seconds % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
  };

  return (
    <div className="flex bg-gray-100 min-h-screen relative">
      <div className="flex-1 p-6 overflow-y-auto" style={{ maxHeight: "100vh" }}>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
           <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-100">
             <h2 className="text-2xl font-bold text-gray-800">Examination #{testId}</h2>
             <div className="flex items-center gap-2 bg-red-50 text-red-600 px-4 py-2 rounded-lg font-bold shadow-inner">
               <Clock className="w-5 h-5"/> {formatTime(timeLeft)}
             </div>
           </div>

           {questions.map((q, i) => (
             <div key={q.id} className="mb-8 pl-4 border-l-4 border-primary-500">
               <p className="text-lg font-semibold text-gray-800 mb-4">Q{i + 1}. {q.question_text}</p>
               <div className="flex flex-col gap-3">
                 {[q.option_a, q.option_b, q.option_c, q.option_d].map((opt, idx) => {
                    const letters = ["A", "B", "C", "D"];
                    return (
                        <label key={idx} className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition w-full">
                            <input type="radio" name={`q_${q.id}`} className="w-4 h-4 text-primary-600" onChange={() => setAnswers({...answers, [q.id]: letters[idx]})} />
                            <span className="text-gray-700">{opt}</span>    
                        </label>
                    )
                 })}
               </div>
             </div>
           ))}

           <button onClick={submitTest} className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 mt-6 rounded-xl shadow-lg transition">Submit Final Answers</button>
        </div>
      </div>

      <div className="w-96 bg-gray-900 border-l border-gray-800 flex flex-col shadow-2xl z-10">
         <div className="p-4 bg-gray-800 flex justify-center items-center gap-2 border-b border-gray-700 shadow-xl">
             <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
             <span className="text-white font-semibold text-sm uppercase tracking-wider">Live Proctoring</span>
         </div>
         <div className="p-4 flex flex-col gap-2">
             {streamActive && (
               <img src={`http://localhost:8000/api/proctor/video_feed?idx=${streamIdx.current}`} className="w-full rounded-xl border border-gray-700 shadow-xl bg-black" style={{minHeight: "220px", objectFit: "cover"}} alt="Proctoring stream loading..." />
             )}
             <div className="mt-4 p-4 bg-red-900/30 border border-red-500/50 rounded-xl text-red-200 text-xs shadow-inner flex items-start gap-2">
                 <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-500"/>
                 <div>
                   <p>Do not look away from the screen. Your webcam feed is analyzed via secure AI models.</p>
                   <p className="mt-2 text-red-400 font-bold">5 Violations = Auto-Submit</p>
                 </div>
             </div>
         </div>
      </div>
    </div>
  );
}