"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ScanFace, Loader2 } from "lucide-react";
import { useVoice } from "../../hooks/useVoice";

export default function AssistantLoginPage() {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const { speak } = useVoice();
  const [statusText, setStatusText] = useState("Checking for previous visits...");
  const initFired = useRef(false);

  useEffect(() => {
    if (initFired.current) return;
    initFired.current = true;
    speak("Namaste. Kripya camere ki taraf dekhein.");
  }, [speak]);

  useEffect(() => {
    let stream: MediaStream | null = null;
    let scanTimeout: NodeJS.Timeout;
    let foundMatch = false;

    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }

        // Give the camera 1.5s to warm up, then scan
        setTimeout(async () => {
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
                foundMatch = true;
                setStatusText(`Welcome back, ${data.patient_name}!`);
                if (stream) stream.getTracks().forEach(track => track.stop());
                setTimeout(() => {
                  router.push(`/department?name=${encodeURIComponent(data.patient_name)}&abha=${encodeURIComponent(data.abha_number)}`);
                }, 1000);
              }
            }
          } catch (err) {
            console.error("Face scan error", err);
          }
        }, 1500);

        // If no match found within 4 seconds total, route to onboarding
        scanTimeout = setTimeout(() => {
          if (!foundMatch) {
            if (stream) stream.getTracks().forEach(track => track.stop());
            router.push('/assistant-onboarding');
          }
        }, 4000);

      } catch (err) {
        console.error("Camera permission denied", err);
        // Fallback to onboarding if no camera
        router.push('/assistant-onboarding');
      }
    };

    startCamera();

    return () => {
      if (stream) stream.getTracks().forEach(track => track.stop());
      clearTimeout(scanTimeout);
    };
  }, [router]);

  return (
    <main className="relative min-h-screen flex flex-col items-center justify-center p-6 bg-slate-950 text-white">
      <div className="absolute inset-0 bg-teal-500/10 blur-[100px] pointer-events-none" />
      
      <div className="z-10 flex flex-col items-center max-w-md w-full text-center">
        <div className="relative w-64 h-64 rounded-full border-4 border-teal-500/30 overflow-hidden flex items-center justify-center bg-slate-900 mb-8 shadow-[0_0_50px_rgba(20,184,166,0.2)]">
          <video 
            ref={videoRef}
            autoPlay 
            playsInline 
            muted 
            className="absolute inset-0 w-full h-full object-cover opacity-60"
          />
          <div className="absolute w-full h-1 bg-teal-400 shadow-[0_0_20px_#2dd4bf] animate-[scan_2s_ease-in-out_infinite] z-10" />
          <ScanFace className="w-20 h-20 text-teal-500/30 absolute z-0" />
        </div>

        <h2 className="text-3xl font-bold mb-4 flex items-center justify-center">
          <Loader2 className="w-8 h-8 mr-3 animate-spin text-teal-400" />
          {statusText}
        </h2>
        <p className="text-slate-400 text-lg">Looking for your profile...</p>
      </div>
    </main>
  );
}
