"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { ArrowLeft, User, ScanFace, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [abhaId, setAbhaId] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);

  // Initialize webcam and face scanning loop
  useEffect(() => {
    let stream: MediaStream | null = null;
    let scanInterval: NodeJS.Timeout;

    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }

        // Scan face every 3 seconds
        scanInterval = setInterval(async () => {
          if (!videoRef.current) return;
          
          const canvas = document.createElement("canvas");
          canvas.width = videoRef.current.videoWidth;
          canvas.height = videoRef.current.videoHeight;
          const ctx = canvas.getContext("2d");
          if (!ctx) return;
          
          ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
          const base64Image = canvas.toDataURL("image/jpeg");

          try {
            const res = await fetch('http://localhost:8000/api/face/match', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ image_base64: base64Image })
            });

            if (res.ok) {
              const data = await res.json();
              if (data.match_found && data.confidence > 0.5) {
                // Stop camera and route on success
                if (stream) stream.getTracks().forEach(track => track.stop());
                clearInterval(scanInterval);
                
                router.push(`/department?name=${encodeURIComponent(data.patient_name)}&abha=${encodeURIComponent(data.abha_number)}`);
              }
            }
          } catch (err) {
            console.error("Face scan error", err);
          }
        }, 3000);
      } catch (err) {
        console.error("Camera permission denied", err);
      }
    };

    startCamera();

    return () => {
      if (stream) stream.getTracks().forEach(track => track.stop());
      clearInterval(scanInterval);
    };
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    
    try {
      const digits = abhaId.replace(/\D/g, '');
      const abhaFormatted = digits.length === 14 ? 
        `${digits.slice(0,2)}-${digits.slice(2,6)}-${digits.slice(6,10)}-${digits.slice(10,14)}` : abhaId;
        
      const res = await fetch(`http://localhost:8000/api/abha/profile/${abhaFormatted}`);
      if (res.ok) {
        const data = await res.json();
        router.push(`/department?name=${encodeURIComponent(data.full_name)}&abha=${encodeURIComponent(data.abha_number)}`);
      } else {
        setErrorMsg("ABHA ID not found. Please try again or create a new profile.");
      }
    } catch (error) {
      setErrorMsg("Failed to connect to backend server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative min-h-screen flex flex-col items-center py-10 px-6">
      <div className="w-full max-w-5xl flex justify-between items-center mb-10">
        <button 
          onClick={() => router.back()}
          className="flex items-center text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="mr-2" /> Back / वापस जाएँ
        </button>
        <h2 className="text-2xl font-bold">Touch Mode</h2>
      </div>

      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-10">
        
        {/* Left Side: Face Recognition (Silent/Fast path) */}
        <div className="glass-panel p-10 rounded-3xl flex flex-col items-center justify-center text-center border-t-4 border-t-teal-500 relative overflow-hidden">
          <div className="w-64 h-64 rounded-full border-4 border-teal-500/50 mb-8 flex items-center justify-center bg-teal-500/5 relative overflow-hidden">
            <video 
              ref={videoRef}
              autoPlay 
              playsInline 
              muted 
              className="absolute inset-0 w-full h-full object-cover opacity-60"
            />
            {/* Scanning animation line */}
            <div className="absolute w-full h-1 bg-teal-400 shadow-[0_0_15px_#2dd4bf] animate-[scan_2.5s_ease-in-out_infinite] z-10" />
            <ScanFace className="w-16 h-16 text-teal-500/30 absolute z-0" />
          </div>
          <h3 className="text-3xl font-semibold mb-2">Look at the Camera</h3>
          <p className="text-teal-400 mb-4">कैमरे की ओर देखें</p>
          <p className="text-slate-400">
            If you have visited before, we will recognize you automatically and log you in.
          </p>
        </div>

        {/* Right Side: Manual ABHA Login */}
        <div className="glass-panel p-10 rounded-3xl border-t-4 border-t-sky-500">
          <h3 className="text-3xl font-semibold mb-2">Enter ABHA Details</h3>
          <p className="text-sky-400 mb-8">अपना आभा (ABHA) विवरण दर्ज करें</p>
          
          <form onSubmit={handleLogin} className="flex flex-col gap-6">
            <div>
              <label className="block text-slate-400 mb-2 font-medium">
                ABHA ID or Mobile Number
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <User className="text-slate-500" />
                </div>
                <input
                  type="text"
                  required
                  value={abhaId}
                  onChange={(e) => setAbhaId(e.target.value)}
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all text-lg"
                  placeholder="e.g. 91-XXXX-XXXX-XXXX"
                />
              </div>
            </div>
            
            <button
              type="submit"
              disabled={loading || !abhaId}
              className="w-full bg-sky-500 hover:bg-sky-400 text-white font-bold py-4 rounded-xl text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-4"
            >
              {loading ? "Verifying..." : "Proceed / आगे बढ़ें"}
            </button>
            {errorMsg && (
              <p className="text-red-400 text-center font-medium mt-2">{errorMsg}</p>
            )}
          </form>

          <div className="mt-8 text-center border-t border-slate-700 pt-6">
            <p className="text-slate-400 mb-4">Don't have an ABHA ID?</p>
            <button 
              onClick={() => router.push('/register')}
              className="text-sky-400 font-medium hover:text-sky-300 flex items-center justify-center w-full"
            >
              Create new ABHA Profile <ArrowRight className="ml-2 w-4 h-4" />
            </button>
          </div>
        </div>

      </div>
    </main>
  );
}
