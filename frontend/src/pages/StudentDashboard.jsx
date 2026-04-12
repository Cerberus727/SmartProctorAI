import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/api";
import { LogOut, PlayCircle, ClipboardList } from "lucide-react";

export default function StudentDashboard() {
  const [tests, setTests] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/test/list").then(res => {
      if(res.data.success) setTests(res.data.data);
    }).catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-64 bg-white shadow-lg flex flex-col">
        <div className="p-6 border-b border-gray-100">
           <h2 className="text-xl font-bold text-primary-700">Student Portal</h2>
        </div>
        <nav className="flex-1 p-4">
          <Link to="#" className="flex items-center gap-3 text-primary-600 bg-primary-50 px-4 py-3 rounded-lg font-medium"><ClipboardList className="w-5 h-5"/> Available Tests</Link>
        </nav>
        <div className="p-4 border-t border-gray-100">
          <button onClick={() => { localStorage.clear(); navigate("/login"); }} className="flex items-center gap-2 text-red-600 font-medium px-4 py-2 hover:bg-red-50 w-full rounded-lg transition"><LogOut className="w-5 h-5"/> Logout</button>
        </div>
      </aside>
      <main className="flex-1 p-8">
        <h1 className="text-3xl font-bold mb-8 text-gray-800">Available Examinations</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tests.map(t => (
            <div key={t.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col hover:shadow-md transition">
               <h3 className="text-xl font-semibold mb-2">{t.title}</h3>
               <p className="text-gray-600 mb-4 flex-1">{t.description}</p>
               <div className="flex justify-between items-center mt-auto">
                 <span className="text-sm text-gray-500 font-medium px-3 py-1 bg-gray-100 rounded-full">{t.duration_minutes} mins</span>
                 <Link to={`/verify/${t.id}`} className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-primary-700 transition">
                   <PlayCircle className="w-4 h-4"/> Start
                 </Link>
               </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
