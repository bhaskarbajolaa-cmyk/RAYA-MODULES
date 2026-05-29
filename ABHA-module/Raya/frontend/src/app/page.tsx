"use client";

import { motion } from "framer-motion";
import { ArrowRight, Video, Mic } from "lucide-react";
import { useRouter } from "next/navigation";

export default function WelcomePage() {
  const router = useRouter();

  return (
    <main className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* Background Ornaments */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-sky-500/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-teal-500/20 blur-[120px] pointer-events-none" />

      {/* Main Content */}
      <div className="z-10 flex flex-col items-center w-full max-w-6xl px-6">
        
        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 w-full">
          {/* Voice Mode */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => router.push('/assistant-login')}
            className="cursor-pointer glass-panel p-14 rounded-3xl relative overflow-hidden group border border-teal-500/30 hover:border-teal-500/60 transition-colors flex flex-col justify-center min-h-[450px]"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-teal-500/10 rounded-full blur-3xl group-hover:bg-teal-500/20 transition-colors" />
            <div className="bg-teal-500/20 p-6 rounded-2xl w-fit mb-8 pulse-ring">
              <Mic className="w-14 h-14 text-teal-400" />
            </div>
            <h3 className="text-4xl md:text-5xl font-semibold mb-3">Voice Assistant</h3>
            <h4 className="text-3xl text-teal-400 font-medium mb-6">वॉइस असिस्टेंट</h4>
            <p className="text-slate-400 text-xl mb-10 leading-relaxed">
              Speak to the AI to generate your token.<br/>
              टोकन बनाने के लिए AI से बात करें।
            </p>
            <div className="flex items-center text-teal-400 font-medium text-2xl mt-auto">
              Start / शुरू करें <ArrowRight className="ml-3 w-8 h-8 group-hover:translate-x-2 transition-transform" />
            </div>
          </motion.div>

          {/* Touch Mode */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => router.push('/login')}
            className="cursor-pointer glass-panel p-14 rounded-3xl relative overflow-hidden group border border-sky-500/30 hover:border-sky-500/60 transition-colors flex flex-col justify-center min-h-[450px]"
          >
             <div className="absolute top-0 right-0 w-32 h-32 bg-sky-500/10 rounded-full blur-3xl group-hover:bg-sky-500/20 transition-colors" />
            <div className="bg-sky-500/20 p-6 rounded-2xl w-fit mb-8">
              <Video className="w-14 h-14 text-sky-400" />
            </div>
            <h3 className="text-4xl md:text-5xl font-semibold mb-3">Touch Screen</h3>
            <h4 className="text-3xl text-sky-400 font-medium mb-6">टच स्क्रीन</h4>
            <p className="text-slate-400 text-xl mb-10 leading-relaxed">
              Use the screen and camera to generate your token.<br/>
              टोकन बनाने के लिए स्क्रीन और कैमरे का उपयोग करें।
            </p>
            <div className="flex items-center text-sky-400 font-medium text-2xl mt-auto">
              Start / शुरू करें <ArrowRight className="ml-3 w-8 h-8 group-hover:translate-x-2 transition-transform" />
            </div>
          </motion.div>
        </div>
      </div>
      
    </main>
  );
}
