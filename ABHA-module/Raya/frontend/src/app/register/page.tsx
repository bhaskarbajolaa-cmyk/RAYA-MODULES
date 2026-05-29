"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, User, Calendar, Phone, CheckCircle, Camera } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  
  const [formData, setFormData] = useState({
    full_name: "",
    aadhaar_number: "",
    gender: "M",
    mobile_number: "",
    preferred_address_prefix: ""
  });

  // Start webcam
  useEffect(() => {
    let stream: MediaStream | null = null;
    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Camera permission denied", err);
      }
    };
    startCamera();
    return () => {
      if (stream) stream.getTracks().forEach(track => track.stop());
    };
  }, []);

  const handleChange = (e: any) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");

    try {
      // 1. Register ABHA Profile
      const abhaRes = await fetch("http://localhost:8000/api/abha/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      
      if (!abhaRes.ok) throw new Error("Failed to create ABHA profile");
      const abhaData = await abhaRes.json();
      
      // 2. Capture face frame
      let base64Image = "";
      if (videoRef.current) {
        const canvas = document.createElement("canvas");
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
          base64Image = canvas.toDataURL("image/jpeg");
        }
      }

      // 3. Register Face Biometrics in RAYA
      if (base64Image) {
        const faceRes = await fetch("http://localhost:8000/api/face/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            abha_number: abhaData.abha_number,
            image_base64: base64Image
          })
        });
        if (!faceRes.ok) console.warn("Failed to enroll biometrics, but ABHA was created");
      }

      setSuccess(true);
      setTimeout(() => {
        router.push(`/department?name=${encodeURIComponent(abhaData.full_name)}&abha=${encodeURIComponent(abhaData.abha_number)}`);
      }, 2000);
      
    } catch (error: any) {
      setErrorMsg(error.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-6 text-center">
        <CheckCircle className="w-24 h-24 text-teal-400 mb-6" />
        <h2 className="text-3xl font-bold mb-4">Registration Successful!</h2>
        <p className="text-slate-400 text-xl">Routing you to department selection...</p>
      </main>
    );
  }

  return (
    <main className="relative min-h-screen flex flex-col items-center py-10 px-6 overflow-y-auto">
      <div className="w-full max-w-5xl flex justify-between items-center mb-10">
        <button 
          onClick={() => router.back()}
          className="flex items-center text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="mr-2" /> Back / वापस जाएँ
        </button>
        <h2 className="text-2xl font-bold">New Patient Registration</h2>
      </div>

      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-10">
        
        {/* Left Side: Form */}
        <div className="glass-panel p-10 rounded-3xl border-t-4 border-t-sky-500">
          <h3 className="text-2xl font-semibold mb-6">Create ABHA ID</h3>
          <form onSubmit={handleRegister} className="flex flex-col gap-4">
            <div>
              <label className="block text-slate-400 mb-1 text-sm">Full Name</label>
              <input type="text" name="full_name" required onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-sky-500" placeholder="John Doe" />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 mb-1 text-sm">Aadhaar Number</label>
                <input type="text" name="aadhaar_number" required onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-sky-500" placeholder="12-digit Aadhaar" />
              </div>
              <div>
                <label className="block text-slate-400 mb-1 text-sm">Gender</label>
                <select name="gender" onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-sky-500">
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="O">Other</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 text-sm">Mobile Number</label>
              <input type="tel" name="mobile_number" required onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-sky-500" placeholder="10-digit number" />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 text-sm">Preferred ABHA Address (e.g. john)</label>
              <div className="flex">
                <input type="text" name="preferred_address_prefix" required onChange={handleChange} className="flex-1 bg-slate-900 border border-slate-700 rounded-l-lg p-3 text-white focus:outline-none focus:border-sky-500" placeholder="johndoe" />
                <div className="bg-slate-800 border border-slate-700 border-l-0 rounded-r-lg p-3 text-slate-400">@abdm</div>
              </div>
            </div>

            <button type="submit" disabled={loading} className="w-full bg-sky-500 hover:bg-sky-400 text-white font-bold py-4 rounded-xl text-lg mt-4 transition-all">
              {loading ? "Registering..." : "Create ABHA & Register"}
            </button>
            {errorMsg && <p className="text-red-400 text-center text-sm">{errorMsg}</p>}
          </form>
        </div>

        {/* Right Side: Face Capture */}
        <div className="glass-panel p-10 rounded-3xl flex flex-col items-center justify-center text-center border-t-4 border-t-teal-500">
          <h3 className="text-2xl font-semibold mb-2">Face Enrollment</h3>
          <p className="text-slate-400 mb-8 text-sm">We will securely save a mathematical representation of your face so you can skip manual login next time.</p>
          
          <div className="w-64 h-64 rounded-2xl border-2 border-teal-500/50 mb-6 overflow-hidden relative bg-slate-900">
            <video 
              ref={videoRef}
              autoPlay 
              playsInline 
              muted 
              className="absolute inset-0 w-full h-full object-cover"
            />
            <div className="absolute inset-0 border-4 border-transparent border-t-teal-400/50 rounded-2xl animate-spin" style={{ animationDuration: '3s' }} />
          </div>
          
          <div className="flex items-center text-teal-400 text-sm font-medium">
            <Camera className="w-4 h-4 mr-2" />
            Camera Active
          </div>
        </div>

      </div>
    </main>
  );
}
