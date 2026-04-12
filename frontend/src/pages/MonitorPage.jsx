import { useEffect, useState } from "react";
import api from "../api/api";

export default function MonitorPage() {
   const [logs, setLogs] = useState([]);

   useEffect(() => {
     const i = setInterval(() => {
        api.get("/proctor/logs").then(res => {
            if(res.data.success && res.data.data) {
                setLogs(res.data.data.reverse());
            }
        });
     }, 2000);
     return () => clearInterval(i);
   }, []);

   return (
       <div className="min-h-screen bg-gray-100 p-8">
           <h1 className="text-3xl font-bold mb-6">Security Monitor Panel</h1>
           <div className="bg-white rounded-xl shadow p-6">
              <h3 className="text-xl font-bold border-b pb-2 mb-4">Live Incident Events</h3>
              <div className="flex flex-col gap-2">
                 {logs.map((L, i) => (
                    <div key={i} className="flex justify-between items-center p-3 bg-red-50 border-l-4 border-red-500 rounded">
                       <div>
                          <span className="font-bold text-red-700">{L.event}</span>
                          <p className="text-sm text-gray-500">Duration: {L.duration}s | Risk Score: {L.risk_score}</p>
                       </div>
                       <span className="text-xs text-gray-400">{new Date(L.start_time).toLocaleTimeString()}</span>
                    </div>
                 ))}
                 {logs.length === 0 && <p className="text-gray-500">No security incidents detected.</p>}
              </div>
           </div>
       </div>
   );
}
