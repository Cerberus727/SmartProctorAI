import { Link } from "react-router-dom";
import { ShieldCheck, MonitorPlay, Users } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow-sm py-4 px-8 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-primary-600 flex items-center gap-2">
          <ShieldCheck className="w-8 h-8"/> ProctorAI
        </h1>
        <Link to="/login" className="bg-primary-600 text-white px-5 py-2 rounded-lg font-medium hover:bg-primary-700 transition">
          Login / Register
        </Link>
      </header>
      <main className="flex-1 flex flex-col items-center justify-center text-center p-8">
        <h2 className="text-5xl font-extrabold text-gray-900 mb-6 tracking-tight">
          Next-Gen AI Exam Proctoring
        </h2>
        <p className="text-xl text-gray-600 max-w-3xl mb-10 leading-relaxed">
          Ensure absolute integrity during remote examinations using our advanced computer vision system. Automatically detects mobile phones, multi-face presence, and gaze deviation in real-time.
        </p>
        <div className="flex gap-4">
          <Link to="/login" className="px-8 py-3 text-lg font-semibold bg-primary-600 text-white rounded-xl shadow hover:bg-primary-700 transition">
            Get Started
          </Link>
        </div>
      </main>
    </div>
  );
}
