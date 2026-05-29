"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Mic, ArrowLeft, Loader2, CheckCircle, MicOff } from "lucide-react";
import { useVoice } from "../../hooks/useVoice";

type AssistantState = 
  "INIT" | "ASK_EXISTING" | "FETCHING" | 
  "REG_NAME" | "REG_GENDER" | "REG_MOBILE" | "REG_SUBMIT" |
  "ASK_SYMPTOMS" | "GENERATING" | "DONE";

export default function AssistantPage() {
  const router = useRouter();
  const { isListening, transcript, startListening, stopListening, speak, resetTranscript } = useVoice();
  
  const [state, setState] = useState<AssistantState>("INIT");
  const [patientInfo, setPatientInfo] = useState<any>(null);
  const [generatedToken, setGeneratedToken] = useState<string>("");
  
  // Registration State
  const [regName, setRegName] = useState("");
  const [regGender, setRegGender] = useState("");
  const [regMobile, setRegMobile] = useState("");

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const initFired = useRef(false);

  const resetIdle = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      stopListening();
      router.push('/');
    }, 60000); 
  };

  useEffect(() => {
    resetIdle();
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      stopListening();
    };
  }, [transcript, state]);

  // Main Conversational State Machine
  useEffect(() => {
    const processState = async () => {
      if (!transcript && state !== "INIT" && state !== "REG_SUBMIT" && state !== "GENERATING") return;
      const text = transcript.toLowerCase();

      switch(state) {
        case "INIT":
          if (initFired.current) return;
          initFired.current = true;
          setTimeout(() => {
            speak("Aapka swagat hai. Apna aabha number ya mobile number bataein. Agar nahi hai, toh 'No' bolein.");
            setState("ASK_EXISTING");
            startListening();
          }, 1000);
          break;

        case "ASK_EXISTING":
          if (text.includes("no") || text.includes("nahi") || text.includes("na")) {
            stopListening();
            speak("Chaliye, aapka naya profile banate hain. Kripya apna poora naam bataein.");
            resetTranscript();
            setState("REG_NAME");
            setTimeout(() => startListening(), 3000);
            return;
          }

          const digits = text.replace(/\D/g, '');
          if (digits.length >= 10) {
            stopListening();
            setState("FETCHING");
            try {
              const abhaFormatted = digits.length === 14 ? 
                `${digits.slice(0,2)}-${digits.slice(2,6)}-${digits.slice(6,10)}-${digits.slice(10,14)}` : digits;
                
              const res = await fetch(`http://localhost:8000/api/abha/profile/${abhaFormatted}`);
              if (res.ok) {
                const data = await res.json();
                setPatientInfo(data);
                speak(`Namaste ${data.full_name}. Aap kis vibhag mein dikhana chahte hain?`);
                resetTranscript();
                setState("ASK_SYMPTOMS");
                setTimeout(() => startListening(), 3000);
              } else {
                speak("Number nahi mila. Naya account banate hain. Kripya apna naam bataein.");
                resetTranscript();
                setState("REG_NAME");
                setTimeout(() => startListening(), 3000);
              }
            } catch (err) {
              speak("Server error.");
              setTimeout(() => router.push('/'), 3000);
            }
          }
          break;

        case "REG_NAME":
          // Wait for the user to speak at least two words (first and last name) ideally,
          // but we will just accept the transcript if it settles.
          if (text.length > 2) {
             stopListening();
             setRegName(transcript);
             speak(`Theek hai ${transcript}. Aapka gender kya hai? Male, ya female?`);
             resetTranscript();
             setState("REG_GENDER");
             setTimeout(() => startListening(), 3000);
          }
          break;

        case "REG_GENDER":
          if (text.includes("male") || text.includes("aadmi") || text.includes("ladka")) {
            stopListening();
            setRegGender("M");
            speak("Theek hai. Apna dus anko ka mobile number bataein.");
            resetTranscript();
            setState("REG_MOBILE");
            setTimeout(() => startListening(), 2000);
          } else if (text.includes("female") || text.includes("aurat") || text.includes("ladki") || text.includes("stri")) {
            stopListening();
            setRegGender("F");
            speak("Theek hai. Apna dus anko ka mobile number bataein.");
            resetTranscript();
            setState("REG_MOBILE");
            setTimeout(() => startListening(), 2000);
          }
          break;

        case "REG_MOBILE":
          const mobDigits = text.replace(/\D/g, '');
          if (mobDigits.length >= 10) {
            stopListening();
            setRegMobile(mobDigits.slice(0, 10));
            setState("REG_SUBMIT");
          }
          break;

        case "REG_SUBMIT":
          try {
            speak("Aapka profile banaya ja raha hai. Pratiksha karein.");
            const res = await fetch('http://localhost:8000/api/abha/register', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                full_name: regName,
                dob: "1990-01-01", // Default for oral flow
                gender: regGender || "M",
                mobile: regMobile,
                address: "Oral Registration",
                face_encoding: "[]"
              })
            });
            
            if (res.ok) {
              const data = await res.json();
              setPatientInfo({
                full_name: data.full_name,
                abha_number: data.abha_number
              });
              speak(`Aapka ABHA profile ban gaya. Ab bataein, aapko kis doctor ko dikhana hai?`);
              resetTranscript();
              setState("ASK_SYMPTOMS");
              setTimeout(() => startListening(), 4000);
            } else {
              speak("Profile nahi ban saka.");
              setTimeout(() => router.push('/'), 3000);
            }
          } catch (e) {
             speak("Error.");
          }
          break;

        case "ASK_SYMPTOMS":
          const keywords: Record<string, string[]> = {
            "Cardiology": ["heart", "dil", "cardio", "chest", "chest pain", "chhati", "dard"],
            "Orthopaedics": ["bone", "haddi", "ortho", "joint", "knee", "pair", "haath"],
            "Ophthalmology": ["eye", "aankh", "vision", "blur"],
            "Dermatology": ["skin", "twacha", "rash", "itch", "khujli", "derma"],
            "Pediatrics": ["child", "baby", "bachcha", "pediatric"],
            "General Medicine": ["general", "fever", "bukhar", "medicine", "cold", "zukaam", "bimar"]
          };

          for (const [dept, words] of Object.entries(keywords)) {
            if (words.some(word => text.includes(word))) {
              stopListening();
              setState("GENERATING");
              
              try {
                const res = await fetch('http://localhost:8000/api/tokens/generate', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    patient_name: patientInfo.full_name,
                    symptoms: dept, 
                    abha_number: patientInfo.abha_number
                  })
                });
                
                if (res.ok) {
                  const data = await res.json();
                  setGeneratedToken(data.token_number);
                  setState("DONE");
                }
              } catch (err) {
                speak("Error. Token nahi ban saka.");
                setTimeout(() => router.push('/'), 3000);
              }
              break;
            }
          }
          break;

        case "DONE":
          if (generatedToken) {
            speak(`Aapka token ban gaya hai. Token number hai ${generatedToken}.`);
            setGeneratedToken("");
            setTimeout(() => {
              router.push('/');
            }, 5000);
          }
          break;
      }
    };

    // Use a slight debounce to prevent running exactly on every keystroke/phoneme
    const handler = setTimeout(() => {
      processState();
    }, 500);

    return () => clearTimeout(handler);
  }, [state, transcript, speak, startListening, stopListening, router, patientInfo, generatedToken, resetTranscript, regName, regGender, regMobile]);

  // UI Helpers
  const getSubtitle = () => {
    switch(state) {
      case "INIT": return "Initializing...";
      case "ASK_EXISTING": return "Tell us your ABHA or Mobile number, or say 'Nahi'";
      case "REG_NAME": return "What is your full name?";
      case "REG_GENDER": return "What is your gender? (Male / Female)";
      case "REG_MOBILE": return "What is your 10-digit mobile number?";
      case "FETCHING": 
      case "REG_SUBMIT": return "Processing data with server...";
      case "ASK_SYMPTOMS": return `Welcome, ${patientInfo?.full_name}. What is your concern?`;
      case "GENERATING": return "Generating Token...";
      case "DONE": return "All done!";
      default: return "";
    }
  };

  const isInteractiveState = ["ASK_EXISTING", "REG_NAME", "REG_GENDER", "REG_MOBILE", "ASK_SYMPTOMS"].includes(state);

  return (
    <main className="relative min-h-screen flex flex-col items-center py-10 px-6">
      
      <div className="w-full max-w-5xl flex justify-between items-center mb-10">
        <button 
          onClick={() => {
            stopListening();
            router.back();
          }}
          className="flex items-center text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="mr-2" /> Exit Voice Mode
        </button>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center max-w-3xl text-center w-full">
        
        {/* Central UI */}
        <div 
          className="relative mb-12 cursor-pointer group" 
          onClick={() => {
             if (isInteractiveState) {
               isListening ? stopListening() : startListening();
             }
          }}
        >
          {isListening && (
            <>
              <div className="absolute inset-0 bg-teal-500 rounded-full blur-[60px] opacity-20 animate-pulse" />
              <div className="absolute inset-0 border-[4px] border-teal-500 rounded-full animate-[ping_2s_ease-out_infinite] opacity-30" />
            </>
          )}
          <div className={`w-48 h-48 rounded-full flex items-center justify-center transition-all duration-500 z-10 relative ${
            isListening ? 'bg-teal-500/20 shadow-[0_0_40px_#2dd4bf]' : 'bg-slate-800 group-hover:bg-slate-700'
          }`}>
            {isListening ? (
              <Mic className="w-24 h-24 text-teal-400 animate-pulse" />
            ) : (
              <MicOff className="w-24 h-24 text-slate-500" />
            )}
          </div>
          
          {/* Action Prompt */}
          {isInteractiveState && (
             <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 w-64 text-teal-400 font-semibold h-6">
               {isListening ? "Listening..." : "Tap to Speak"}
             </div>
          )}
        </div>

        {/* Dynamic Title */}
        <h2 className="text-3xl font-bold mb-4 text-white">
          {getSubtitle()}
        </h2>

        {/* Live Transcript / Feedback */}
        <div className="h-24 flex items-center justify-center w-full bg-slate-900/50 rounded-2xl p-6 border border-slate-800">
          {isInteractiveState ? (
            <p className={`text-3xl font-medium italic ${transcript ? 'text-teal-400' : 'text-slate-500'}`}>
              {transcript ? `"${transcript}"` : "Waiting for voice..."}
            </p>
          ) : (
            <div className="flex items-center text-slate-400">
              {["FETCHING", "REG_SUBMIT", "GENERATING"].includes(state) ? (
                <Loader2 className="animate-spin w-10 h-10 text-teal-400" />
              ) : null}
              {state === "DONE" ? <CheckCircle className="w-14 h-14 text-emerald-400" /> : null}
            </div>
          )}
        </div>

      </div>
    </main>
  );
}
