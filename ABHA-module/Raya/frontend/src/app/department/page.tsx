"use client";

import { motion } from "framer-motion";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, HeartPulse, Bone, Eye, Sparkles, Stethoscope, Baby } from "lucide-react";

const DEPARTMENTS = [
  { id: "Cardiology", name: "Cardiology", hindi: "हृदय रोग", icon: HeartPulse, color: "text-rose-500", bg: "bg-rose-500/10" },
  { id: "Orthopaedics", name: "Orthopaedics", hindi: "हड्डी रोग", icon: Bone, color: "text-amber-500", bg: "bg-amber-500/10" },
  { id: "Ophthalmology", name: "Ophthalmology", hindi: "नेत्र रोग", icon: Eye, color: "text-blue-500", bg: "bg-blue-500/10" },
  { id: "Dermatology", name: "Dermatology", hindi: "त्वचा रोग", icon: Sparkles, color: "text-purple-500", bg: "bg-purple-500/10" },
  { id: "Pediatrics", name: "Pediatrics", hindi: "बाल रोग", icon: Baby, color: "text-emerald-500", bg: "bg-emerald-500/10" },
  { id: "General Medicine", name: "General Medicine", hindi: "सामान्य चिकित्सा", icon: Stethoscope, color: "text-teal-500", bg: "bg-teal-500/10" },
];

import { useEffect, useRef, useState } from "react";
import { User, Mic, MicOff, Loader2 } from "lucide-react";
import { useVoice } from "../../hooks/useVoice";

export default function DepartmentPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const patientName = searchParams.get('name') || "Guest_Patient";
  const abha = searchParams.get('abha') || "";
  
  const { isListening, transcript, startListening, stopListening, resetTranscript, speak } = useVoice();
  const [isProcessing, setIsProcessing] = useState(false);

  // 30-second idle timeout for touch UI
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const resetTimeout = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      router.push('/');
    }, 60000); 
  };

  useEffect(() => {
    resetTimeout();
    window.addEventListener('mousemove', resetTimeout);
    window.addEventListener('keydown', resetTimeout);
    window.addEventListener('touchstart', resetTimeout);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      window.removeEventListener('mousemove', resetTimeout);
      window.removeEventListener('keydown', resetTimeout);
      window.removeEventListener('touchstart', resetTimeout);
    };
  }, [router]);

  const handleSelect = (dept: string) => {
    router.push(`/token?dept=${dept}&name=${patientName}&abha=${abha}`);
  };

  const handleRecordToggle = async () => {
    if (isListening) {
      stopListening();
      if (transcript.length > 3) {
        setIsProcessing(true);
        speak("Aapki samasya process ho rahi hai.");
        // Find best department based on symptoms locally
        const text = transcript.toLowerCase();
        let bestDept = "General Medicine";
        const keywords: Record<string, string[]> = {
          "Cardiology": ["heart", "dil", "cardio", "chest", "chest pain", "chhati", "dard"],
          "Orthopaedics": ["bone", "haddi", "ortho", "joint", "knee", "pair", "haath"],
          "Ophthalmology": ["eye", "aankh", "vision", "blur"],
          "Dermatology": ["skin", "twacha", "rash", "itch", "khujli", "derma"],
          "Pediatrics": ["child", "baby", "bachcha", "pediatric"]
        };
        for (const [dept, words] of Object.entries(keywords)) {
          if (words.some(word => text.includes(word))) {
            bestDept = dept;
            break;
          }
        }
        
        // Pass it to the token screen (it handles generating and printing)
        router.push(`/token?dept=${bestDept}&name=${patientName}&abha=${abha}`);
      } else {
        speak("Aapki aawaz theek se sunai nahi di. Phir try karein.");
        resetTranscript();
      }
    } else {
      resetTranscript();
      startListening();
    }
  };

  return (
    <main className="relative min-h-screen flex flex-col items-center py-10 px-6 overflow-hidden">
      
      {/* Top Header with Back button and User Info */}
      <div className="w-full max-w-5xl flex justify-between items-center mb-10 z-10">
        <button 
          onClick={() => router.back()}
          className="flex items-center text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="mr-2" /> Back / वापस जाएँ
        </button>

        {/* User Indication Top Right */}
        <div className="flex items-center bg-slate-800/50 px-4 py-2 rounded-full border border-slate-700 shadow-lg">
          <User className="w-5 h-5 text-teal-400 mr-2" />
          <span className="text-white font-medium">
            Welcome, <span className="text-teal-400">{patientName}</span>
          </span>
        </div>
      </div>

      <div className="text-center mb-10 relative z-10">
        <h2 className="text-3xl font-bold mb-2">Select Department or Record Symptoms</h2>
        <p className="text-sky-400">विभाग चुनें या अपनी समस्या रिकॉर्ड करें</p>
      </div>

      {/* Manual Department Grid */}
      <div className="w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-32 z-10">
        {DEPARTMENTS.map((dept, idx) => {
          const Icon = dept.icon;
          return (
            <motion.div
              key={dept.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleSelect(dept.id)}
              className="glass-panel p-6 rounded-3xl cursor-pointer hover:border-slate-600 transition-all group flex flex-col items-center text-center"
            >
              <div className={`${dept.bg} ${dept.color} p-4 rounded-2xl mb-4 group-hover:scale-110 transition-transform`}>
                <Icon className="w-10 h-10" />
              </div>
              <h3 className="text-xl font-bold mb-1">{dept.name}</h3>
              <h4 className="text-lg text-slate-400">{dept.hindi}</h4>
            </motion.div>
          );
        })}
      </div>

      {/* Floating Push-to-Talk Record Button */}
      <div className="fixed bottom-0 left-0 w-full bg-slate-900/80 backdrop-blur-md border-t border-slate-800 p-6 flex flex-col items-center z-50">
        <div className="flex items-center justify-center gap-6">
          <button
            onClick={handleRecordToggle}
            className={`relative flex items-center justify-center w-20 h-20 rounded-full transition-all duration-300 ${
              isListening ? 'bg-rose-500/20 border-4 border-rose-500 animate-pulse' : 'bg-teal-500 hover:bg-teal-400'
            }`}
          >
            {isProcessing ? (
               <Loader2 className="w-8 h-8 text-white animate-spin" />
            ) : isListening ? (
               <Mic className="w-10 h-10 text-rose-400" />
            ) : (
               <Mic className="w-10 h-10 text-white" />
            )}
          </button>
          
          <div className="flex flex-col">
             <span className="text-xl font-bold text-white">
               {isListening ? "Listening..." : "Or Tap to Explain Your Problem"}
             </span>
             <span className="text-slate-400 italic">
               {isListening && transcript ? `"${transcript}"` : (isListening ? "Speak now, tap again to stop..." : "Bataein aapko kya samasya hai")}
             </span>
          </div>
        </div>
      </div>
      
    </main>
  );
}
