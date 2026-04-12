import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api";
import { ShieldAlert } from "lucide-react";

export default function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", password: "", role: "student" });
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isRegister) {
        await api.post("/auth/register", {
          name: formData.name,
          email: formData.email,
          password: formData.password,
          role: formData.role
        });
        alert("Registered! Please login.");
        setIsRegister(false);
      } else {
        const res = await api.post("/auth/login", {
          email: formData.email,
          password: formData.password
        });
        localStorage.setItem("token", res.data.access_token);
        localStorage.setItem("role", res.data.role);
        localStorage.setItem("user_id", res.data.user_id);
        
        if (res.data.role === "admin") navigate("/admin");
        else navigate("/student");
      }
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.response?.data?.message;
      const errorMsg = typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail) || "Authentication Failed";
      alert("Error: " + errorMsg);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-primary-100 p-3 rounded-full mb-2">
             <ShieldAlert className="w-8 h-8 text-primary-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800">{isRegister ? "Create Account" : "Welcome Back"}</h2>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {isRegister && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input required type="text" className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:outline-none" 
                onChange={e => setFormData({...formData, name: e.target.value})} />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input required type="email" className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:outline-none" 
              onChange={e => setFormData({...formData, email: e.target.value})} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input required type="password" className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:outline-none" 
              onChange={e => setFormData({...formData, password: e.target.value})} />
          </div>
          {isRegister && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:outline-none" onChange={e => setFormData({...formData, role: e.target.value})}>
                <option value="student">Student</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          )}
          <button type="submit" className="w-full bg-primary-600 text-white font-bold py-2.5 rounded-lg mt-2 hover:bg-primary-700 transition">
            {isRegister ? "Register" : "Login"}
          </button>
        </form>
        <p className="text-center text-sm text-gray-600 mt-6">
          {isRegister ? "Already have an account?" : "Don't have an account?"}
          <button type="button" onClick={() => setIsRegister(!isRegister)} className="ml-1 text-primary-600 font-semibold hover:underline border-none bg-transparent cursor-pointer">
            {isRegister ? "Login here" : "Register here"}
          </button>
        </p>
      </div>
    </div>
  );
}
