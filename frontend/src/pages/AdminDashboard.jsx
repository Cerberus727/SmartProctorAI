import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/api";
import { FileText, Activity, Trash2, Clock, CheckCircle, Search, AlertCircle, Eye } from "lucide-react";  
import toast from "react-hot-toast";

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [tests, setTests] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [activeTab, setActiveTab] = useState("tests"); // "tests" or "submissions"
  const [selectedLog, setSelectedLog] = useState(null); // to show modal for logs

  const fetchTests = async () => {
    try {
      const res = await api.get("/test/list");
      if (res.data.success) {
         setTests(res.data.data.reverse()); // latest first
      }
    } catch(err) {
      toast.error("Failed to load tests");
    }
  };

  const fetchSubmissions = async () => {
    try {
      const res = await api.get("/test/submissions");
      if (res.data.success) {
         setSubmissions(res.data.data);
      }
    } catch(err) {
      toast.error("Failed to load submissions");
    }
  };

  useEffect(() => {
    fetchTests();
    fetchSubmissions();
  }, []);

  const handleDelete = async (id) => {
    if(!window.confirm("Are you sure you want to delete this test? All related submissions and logs will be permanently deleted.")) return;
    try {
      await api.delete(`/test/${id}`);
      toast.success("Test deleted successfully!");
      fetchTests();
    } catch (err) {
      toast.error("Failed to delete test.");
    }
  };

  return (
     <div className="min-h-screen bg-gray-50 flex flex-col">
       <header className="bg-white shadow py-4 px-8 flex justify-between items-center border-b-4 border-primary-500 relative z-10">
         <h1 className="text-2xl font-bold text-gray-800">Admin Dashboard</h1>  
         <button onClick={() => { localStorage.clear(); navigate("/"); }} className="text-red-600 font-medium hover:underline">Logout</button>
       </header>
       <main className="p-10 flex flex-col gap-10 max-w-7xl mx-auto w-full flex-1">    

         {/* Quick Actions */}
         <div className="flex gap-6">
           <Link to="/admin/create-test" className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex-1 flex items-center p-8 gap-6 hover:shadow-md hover:-translate-y-1 transition duration-300">
              <div className="p-5 bg-blue-100 text-primary-600 rounded-full"><FileText className="w-10 h-10"/></div>
              <div>
                 <h3 className="text-2xl font-bold text-gray-800">Create Custom Test</h3>
                 <p className="text-gray-500 mt-1">Design a new assessment with custom questions.</p>
              </div>
           </Link>

           <Link to="/monitor" className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex-1 flex items-center p-8 gap-6 hover:shadow-md hover:-translate-y-1 transition duration-300">
              <div className="p-5 bg-red-100 text-red-600 rounded-full"><Activity className="w-10 h-10"/></div>
              <div>
                 <h3 className="text-2xl font-bold text-gray-800">Live Monitor</h3>
                 <p className="text-gray-500 mt-1">Watch active student proctoring logs & streams.</p>
              </div>
           </Link>
         </div>

         {/* Tab Navigation */}
         <div className="flex bg-white rounded-xl border border-gray-200 p-1 shadow-sm w-fit">
           <button 
             onClick={() => setActiveTab('tests')} 
             className={`px-6 py-2 rounded-lg font-bold transition flex justify-center items-center gap-2 ${activeTab === 'tests' ? 'bg-primary-50 text-primary-600' : 'text-gray-500 hover:bg-gray-50'}`}
           >
             <CheckCircle className="w-5 h-5"/> Manage Tests
           </button>
           <button 
             onClick={() => setActiveTab('submissions')} 
             className={`px-6 py-2 rounded-lg font-bold transition flex justify-center items-center gap-2 ${activeTab === 'submissions' ? 'bg-primary-50 text-primary-600' : 'text-gray-500 hover:bg-gray-50'}`}
           >
             <FileText className="w-5 h-5"/> Student Submissions & Reports
           </button>
         </div>

         {/* Tests View */}
         {activeTab === 'tests' && (
         <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
           {tests.length === 0 ? (
             <div className="bg-white p-10 text-center rounded-2xl border border-dashed border-gray-300 text-gray-500">
               No tests created yet. Click "Create Custom Test" to get started. 
             </div>
           ) : (
             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {tests.map(t => (
                  <div key={t.id} className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition flex flex-col">   
                     <div className="p-6 flex-1">
                        <h3 className="text-xl font-bold text-gray-800 mb-2 truncate" title={t.title}>{t.title}</h3>
                        <div className="flex flex-col gap-2 mt-4 text-sm text-gray-600 font-medium">
                           <div className="flex justify-between items-center bg-gray-50 p-2 rounded">
                              <span className="flex items-center gap-2"><FileText className="w-4 h-4 text-primary-500"/> Questions</span>
                              <span className="font-bold text-gray-800">{t.question_count}</span>
                           </div>
                           <div className="flex justify-between items-center bg-gray-50 p-2 rounded">
                              <span className="flex items-center gap-2"><Clock className="w-4 h-4 text-green-500"/> Duration</span>
                              <span className="font-bold text-gray-800">{t.duration} mins</span>
                           </div>
                        </div>
                     </div>
                     <div className="bg-gray-50 px-6 py-4 flex gap-3 border-t border-gray-100">
                        <Link to={`/test/${t.id}`} className="flex items-center justify-center gap-2 flex-1 bg-blue-100 text-blue-600 hover:bg-blue-200 py-2 rounded-lg font-bold transition">
                           <FileText className="w-4 h-4"/> Preview
                        </Link>
                        <button onClick={() => handleDelete(t.id)} className="flex items-center justify-center gap-2 flex-1 bg-red-100 text-red-600 hover:bg-red-200 py-2 rounded-lg font-bold transition">
                           <Trash2 className="w-4 h-4"/> Delete
                        </button>
                     </div>
                  </div>
                ))}
             </div>
           )}
         </div>
         )}
         
         {/* Submissions View */}
         {activeTab === 'submissions' && (
           <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-500">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                   <thead>
                      <tr className="bg-gray-50 text-gray-600 uppercase text-sm leading-normal border-b border-gray-200">
                         <th className="py-4 px-6 font-bold">Student</th>
                         <th className="py-4 px-6 font-bold">Test Name</th>
                         <th className="py-4 px-6 font-bold">Submitted At</th>
                         <th className="py-4 px-6 font-bold">Score</th>
                         <th className="py-4 px-6 font-bold">Violations</th>
                         <th className="py-4 px-6 font-bold">Action</th>
                      </tr>
                   </thead>
                   <tbody className="text-gray-700 text-sm">
                      {submissions.length === 0 && (
                        <tr>
                          <td colSpan="6" className="py-8 text-center text-gray-500">No submissions found.</td>
                        </tr>
                      )}
                      {submissions.map((sub) => (
                         <tr key={sub.id} className="border-b border-gray-100 hover:bg-gray-50/50">
                            <td className="py-4 px-6 font-semibold text-gray-900">{sub.user_name}</td>
                            <td className="py-4 px-6">{sub.test_title}</td>
                            <td className="py-4 px-6">{new Date(sub.submitted_at).toLocaleString()}</td>
                            <td className="py-4 px-6 font-bold text-primary-600">{sub.score}</td>
                            <td className="py-4 px-6">
                               <span className={`px-3 py-1 rounded-full text-xs font-bold ${sub.violations?.length > 0 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
                                 {sub.violations?.length || 0} violations
                               </span>
                            </td>
                            <td className="py-4 px-6">
                               <button 
                                 onClick={() => setSelectedLog(sub)}
                                 className="flex items-center gap-2 bg-blue-50 text-blue-600 hover:bg-blue-100 px-3 py-1 rounded-lg font-semibold transition"
                               >
                                  <Eye className="w-4 h-4"/> View Report
                               </button>
                            </td>
                         </tr>
                      ))}
                   </tbody>
                </table>
              </div>
           </div>
         )}
       </main>

       {/* Log Modal */}
       {selectedLog && (
         <div className="fixed inset-0 bg-black/60 backdrop-blur-sm shadow z-50 flex justify-center items-center p-4 animate-in fade-in duration-200">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
               <div className="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                  <div>
                    <h2 className="text-xl font-bold text-gray-800">Proctoring Report</h2>
                    <p className="text-sm text-gray-500 font-medium">Student: <span className="text-gray-900">{selectedLog.user_name}</span> | Test: <span className="text-gray-900">{selectedLog.test_title}</span></p>
                  </div>
                  <button onClick={() => setSelectedLog(null)} className="text-gray-400 hover:text-gray-800 transition">
                     <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  </button>
               </div>
               
               <div className="p-6 overflow-y-auto flex-1">
                  <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                     <AlertCircle className="w-5 h-5 text-red-500" /> Detected Incidents ({selectedLog.violations?.length || 0})
                  </h3>
                  
                  {(!selectedLog.violations || selectedLog.violations.length === 0) ? (
                    <div className="bg-green-50 p-6 rounded-xl border border-green-200 text-center text-green-700 font-semibold shadow-inner">
                       í¾‰ No violations were detected during this examination.
                    </div>
                  ) : (
                    <ul className="space-y-3">
                       {selectedLog.violations.map((v, idx) => (
                         <li key={idx} className="flex gap-4 p-4 border border-red-100 bg-red-50/50 rounded-xl items-start">
                           <div className="bg-red-100 p-2 rounded-lg text-red-600">
                              <AlertCircle className="w-5 h-5" />
                           </div>
                           <div>
                              <p className="font-bold text-red-900">{v.event_type.replace(/_/g, ' ')}</p>
                              <p className="text-sm text-red-700 font-medium">{new Date(v.timestamp).toLocaleString()}</p>
                           </div>
                         </li>
                       ))}
                    </ul>
                  )}
               </div>
               
               <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end">
                  <button onClick={() => setSelectedLog(null)} className="px-6 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold rounded-xl transition">Close Report</button>
               </div>
            </div>
         </div>
       )}
     </div>
  );
}
