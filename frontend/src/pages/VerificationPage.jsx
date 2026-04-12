import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { AlertCircle, CheckCircle2, ShieldCheck, Loader2 } from "lucide-react";
import api from "../api/api";
import toast from "react-hot-toast";

export default function VerificationPage() {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);
  const [required, setRequired] = useState(10);
  const [status, setStatus] = useState("INITIALIZING"); // INITIALIZING, VERIFIED, ERROR
  const wsRef = useRef(null);
  const streamIdx = useRef(Math.random());

  useEffect(() => {
    let active = true;

    const initProctoring = async () => {
      try {
        // Start the proctor engine backend so it grabs the local camera and processes frames
        await api.post("/proctor/start");
        
        // Connect WebSocket to listen for Verification progress
        if (active) connectWebSocket();
      } catch (err) {
        console.error("Proctoring start error:", err);
      }
    };

    const connectWebSocket = () => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//localhost:8000/ws`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
         console.log("Verification WS Connected");
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.event === "INITIALIZING" || data.status === "INITIALIZING") {
             setStatus("INITIALIZING");
             if (data.progress !== undefined) setProgress(data.progress);
             if (data.required !== undefined) setRequired(data.required);
          } else if (data.event === "VERIFICATION_COMPLETE" || data.status === "VERIFIED") {
             setStatus("VERIFIED");
             setProgress(required); // fill bar
             
             cleanup();
             setTimeout(() => {
               if(active) navigate(`/test/${testId}`);
             }, 1500);
          }
        } catch (e) {
            console.error("WS Parse error", e);
        }
      };

      wsRef.current.onerror = (err) => {
          console.error("WS Error", err);
      };
    };

    const cleanup = () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };

    initProctoring();

    return () => {
      active = false;
      cleanup();
    };
  }, [testId, navigate, required]);

  const percent = Math.min(100, Math.round((progress / required) * 100)) || 0;

  return (
    <div className="flex bg-gray-100 min-h-screen relative w-full items-center justify-center p-4">
      <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-200 max-w-lg w-full text-center z-10">
        
        <div className="flex justify-center mb-6">
           <div className="bg-primary-50 p-4 rounded-full text-primary-600">
             <ShieldCheck className="w-12 h-12" />
           </div>
        </div>

        <h2 className="text-2xl font-bold text-gray-800 mb-2">AI Proctoring Verification</h2>
        <p className="text-gray-500 mb-8 text-sm">
          Please position your face clearly in the center of the camera. The system is securely associating your identity for this session.
        </p>

        {/* Video Preview - Using MJPEG Stream to prevent camera locks! */}
        <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden shadow-inner mb-8 border-2 border-gray-100">
          {status === "ERROR" ? (
             <div className="absolute inset-0 flex flex-col items-center justify-center text-red-500 bg-red-50">
                <AlertCircle className="w-8 h-8 mb-2" />
                <span className="font-semibold">Camera Error</span>
             </div>
          ) : status === "VERIFIED" ? (
             <div className="absolute inset-0 flex flex-col items-center justify-center text-green-500 bg-green-50 z-10 animate-fade-in">
                <CheckCircle2 className="w-16 h-16 mb-4" />
                <span className="text-xl font-bold">Identity Verified!</span>
             </div>
          ) : (
            <img 
              src={`http://localhost:8000/api/proctor/video_feed?idx=${streamIdx.current}`} 
              className="w-full h-full object-cover" 
              alt="Proctoring stream loading..." 
            />
          )}
        </div>

        {/* Progress Section */}
        {status !== "ERROR" && (
            <div className="space-y-4">
            <div className="flex justify-between text-sm font-semibold text-gray-700">
                <span>{status === "VERIFIED" ? "Verification Complete" : "Capturing Face Reference"}</span>
                <span>{progress} / {required}</span>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden shadow-inner">
                <div 
                className={`h-full transition-all duration-500 ease-out ${status === "VERIFIED" ? 'bg-green-500' : 'bg-primary-600'}`}
                style={{ width: `${percent}%` }}
                ></div>
            </div>

            {status === "INITIALIZING" && (
                <div className="flex items-center justify-center gap-2 text-primary-600 text-sm font-medium mt-4">
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing facial embeddings...
                </div>
            )}
            </div>
        )}

      </div>
    </div>
  );
}