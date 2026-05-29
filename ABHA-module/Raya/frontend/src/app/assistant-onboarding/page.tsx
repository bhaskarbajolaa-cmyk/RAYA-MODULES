"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Mic, ArrowLeft, Loader2, CheckCircle, MicOff, Check, X } from "lucide-react";
import { useVoice } from "../../hooks/useVoice";

type OnboardingState = 
  "INIT" | 
  "AADHAAR_RECORDING" | "AADHAAR_CONFIRM" | 
  "MOBILE_RECORDING" | "MOBILE_CONFIRM" | 
  "OTP_RECORDING" | "OTP_CONFIRM" | 
  "SUBMIT" | "DONE";

export default function AssistantOnboardingPage() {
  const router = useRouter();
  const { isListening, transcript, startListening, stopListening, speak, resetTranscript } = useVoice();
  
  const [state, setState] = useState<OnboardingState>("INIT");
  const [aadhaar, setAadhaar] = useState("");
  const [mobile, setMobile] = useState("");
  const [otp, setOtp] = useState("");
  
  const initFired = useRef(false);

  useEffect(() => {
    if (state === "INIT") {
      if (initFired.current) return;
      initFired.current = true;
      setTimeout(() => {
        speak("Aap naye lag rahe hain. Kripya apna aadhaar number record karein. Neeche diye button ko dabayein.");
        setState("AADHAAR_RECORDING");
      }, 1000);
    }
  }, [state, speak]);

  const handleRecordToggle = () => {
    if (isListening) {
      stopListening();
      // Transition to confirm state based on current recording state
      if (state === "AADHAAR_RECORDING") {
        const digits = transcript.replace(/\D/g, '');
        if (digits.length >= 10) {
          setAadhaar(digits);
          speak(`Aapne kaha ${digits}. Kya ye sahi hai? Confirm dabayein.`);
          setState("AADHAAR_CONFIRM");
        } else {
          speak("Number samajh nahi aaya. Kripya wapas record karein.");
          resetTranscript();
        }
      } else if (state === "MOBILE_RECORDING") {
        const digits = transcript.replace(/\D/g, '');
        if (digits.length >= 10) {
          setMobile(digits.slice(0,10));
          speak(`Aapka mobile hai ${digits.slice(0,10)}. Kya ye sahi hai?`);
          setState("MOBILE_CONFIRM");
        } else {
          speak("Mobile number theek nahi hai. Wapas record karein.");
          resetTranscript();
        }
      } else if (state === "OTP_RECORDING") {
        const digits = transcript.replace(/\D/g, '');
        if (digits.length > 0) {
          setOtp(digits);
          speak(`Aapka OTP hai ${digits}. Kya ye sahi hai?`);
          setState("OTP_CONFIRM");
        } else {
          speak("OTP theek nahi hai. Wapas record karein.");
          resetTranscript();
        }
      }
    } else {
      resetTranscript();
      startListening();
    }
  };

  const handleConfirm = async () => {
    if (state === "AADHAAR_CONFIRM") {
      speak("Dhanyawad. Ab apna dus anko ka mobile number record karein.");
      resetTranscript();
      setState("MOBILE_RECORDING");
    } else if (state === "MOBILE_CONFIRM") {
      speak("Aapke mobile par OTP bheja gaya hai. Kripya record button daba kar OTP bataein.");
      resetTranscript();
      setState("OTP_RECORDING");
    } else if (state === "OTP_CONFIRM") {
      setState("SUBMIT");
      speak("Aapka khata banaya ja raha hai. Pratiksha karein.");
      
      try {
        const res = await fetch('http://localhost:8000/api/abha/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name: "Voice User",
            date_of_birth: "1990-01-01",
            gender: "M",
            mobile_number: mobile,
            preferred_address_prefix: "voice_user"
          })
        });
        
        if (res.ok) {
          const data = await res.json();
          speak(`Aapka profile ban gaya. Ab aap department select kar sakte hain.`);
          setState("DONE");
          setTimeout(() => {
             router.push(`/department?name=${encodeURIComponent(data.full_name)}&abha=${encodeURIComponent(data.abha_number)}`);
          }, 4000);
        } else {
          speak("Server error, wapas try karein.");
          setState("MOBILE_RECORDING");
        }
      } catch (e) {
        speak("Connection error.");
        setState("MOBILE_RECORDING");
      }
    }
  };

  const handleRetry = () => {
    resetTranscript();
    if (state === "AADHAAR_CONFIRM") setState("AADHAAR_RECORDING");
    if (state === "MOBILE_CONFIRM") setState("MOBILE_RECORDING");
    if (state === "OTP_CONFIRM") setState("OTP_RECORDING");
  };

  const getTitle = () => {
    switch (state) {
      case "INIT": return "Starting Assistant...";
      case "AADHAAR_RECORDING": return "Step 1: Record Aadhaar";
      case "AADHAAR_CONFIRM": return "Verify Aadhaar";
      case "MOBILE_RECORDING": return "Step 2: Record Mobile";
      case "MOBILE_CONFIRM": return "Verify Mobile";
      case "OTP_RECORDING": return "Step 3: Record OTP";
      case "OTP_CONFIRM": return "Verify OTP";
      case "SUBMIT": return "Creating Profile...";
      case "DONE": return "Profile Created!";
    }
  };

  const isConfirmState = state.includes("CONFIRM");

  return (
    <main className="relative min-h-screen flex flex-col items-center py-10 px-6 bg-slate-950 text-white">
      
      <div className="w-full max-w-5xl flex justify-between items-center mb-10">
        <button 
          onClick={() => {
            stopListening();
            router.push('/');
          }}
          className="flex items-center text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="mr-2" /> Cancel / रद्द करें
        </button>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center max-w-3xl text-center w-full">
        
        <h2 className="text-3xl font-bold mb-12 text-white">
          {getTitle()}
        </h2>
        
        {!isConfirmState && state !== "SUBMIT" && state !== "DONE" && (
          <div className="flex flex-col items-center mb-12">
            <div 
              className="relative cursor-pointer group" 
              onClick={handleRecordToggle}
            >
              {isListening && (
                <>
                  <div className="absolute inset-0 bg-rose-500 rounded-full blur-[60px] opacity-30 animate-pulse" />
                  <div className="absolute inset-0 border-[6px] border-rose-500 rounded-full animate-ping opacity-40" />
                </>
              )}
              <div className={`w-48 h-48 rounded-full flex items-center justify-center transition-all duration-300 z-10 relative ${
                isListening ? 'bg-rose-500/20 shadow-[0_0_50px_#f43f5e]' : 'bg-slate-800 group-hover:bg-slate-700 border-4 border-slate-600'
              }`}>
                {isListening ? (
                  <Mic className="w-24 h-24 text-rose-400 animate-pulse" />
                ) : (
                  <MicOff className="w-24 h-24 text-slate-500" />
                )}
              </div>
            </div>
            
            <p className="mt-8 text-2xl font-medium text-slate-400">
              {isListening ? "Listening... Tap to Stop" : "Tap Mic to Record"}
            </p>
          </div>
        )}

        {isConfirmState && (
          <div className="flex flex-col items-center mb-12 w-full">
            <div className="bg-slate-900 border border-slate-700 p-8 rounded-3xl w-full max-w-lg mb-8 shadow-2xl">
              <p className="text-slate-400 mb-2 text-lg">Did you say:</p>
              <p className="text-4xl font-bold text-sky-400 tracking-wider">
                {state === "AADHAAR_CONFIRM" && aadhaar}
                {state === "MOBILE_CONFIRM" && mobile}
                {state === "OTP_CONFIRM" && otp}
              </p>
            </div>
            
            <div className="flex gap-6 w-full max-w-lg">
              <button 
                onClick={handleRetry}
                className="flex-1 bg-slate-800 hover:bg-slate-700 text-white font-bold py-5 rounded-2xl text-xl flex items-center justify-center transition-colors border border-slate-600"
              >
                <X className="mr-2" /> Retry
              </button>
              <button 
                onClick={handleConfirm}
                className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-white font-bold py-5 rounded-2xl text-xl flex items-center justify-center transition-colors shadow-[0_0_20px_rgba(16,185,129,0.3)]"
              >
                <Check className="mr-2" /> Confirm
              </button>
            </div>
          </div>
        )}

        {(state === "SUBMIT" || state === "DONE") && (
          <div className="flex flex-col items-center mb-12">
            {state === "SUBMIT" ? (
              <Loader2 className="w-24 h-24 text-teal-400 animate-spin mb-6" />
            ) : (
              <CheckCircle className="w-24 h-24 text-emerald-400 mb-6" />
            )}
            <p className="text-xl text-slate-300">
              {state === "SUBMIT" ? "Generating ABHA Profile..." : "Routing to Department Selection..."}
            </p>
          </div>
        )}

        {/* Live Transcript Display */}
        {isListening && (
          <div className="h-20 flex items-center justify-center w-full max-w-lg bg-slate-900/80 rounded-2xl p-4 border border-slate-700">
            <p className="text-2xl font-medium italic text-rose-400">
              {transcript ? `"${transcript}"` : "..."}
            </p>
          </div>
        )}

      </div>
    </main>
  );
}
