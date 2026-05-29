"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Users, List, RefreshCw, CheckCircle, Trash2, Filter } from "lucide-react";

export default function AdminDashboard() {
  const [tokens, setTokens] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDept, setSelectedDept] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [tokenRes, userRes] = await Promise.all([
        fetch("http://localhost:8000/api/tokens/queue"),
        fetch("http://localhost:8000/api/users/")
      ]);
      if (tokenRes.ok) setTokens(await tokenRes.json());
      if (userRes.ok) setUsers(await userRes.json());
    } catch (err) {
      console.error("Failed to fetch admin data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCompleteToken = async (token_number: string) => {
    // This will mark the token as COMPLETED, removing it from the active WAITING queue.
    try {
      await fetch(`http://localhost:8000/api/tokens/queue/${token_number}/complete`, { method: "PUT" });
      fetchData();
    } catch (err) {
      console.error("Failed to complete token", err);
    }
  };

  const handleDeleteToken = async (token_number: string) => {
    if (!confirm("Are you sure you want to permanently delete this token?")) return;
    try {
      await fetch(`http://localhost:8000/api/tokens/queue/${token_number}`, { method: "DELETE" });
      fetchData();
    } catch (err) {
      console.error("Failed to delete token", err);
    }
  };

  const handleDeleteUser = async (user_id: number) => {
    if (!confirm("Are you sure you want to delete this enrolled biometric profile?")) return;
    try {
      await fetch(`http://localhost:8000/api/users/${user_id}`, { method: "DELETE" });
      fetchData();
    } catch (err) {
      console.error("Failed to delete user", err);
    }
  };

  // Fixed list of departments
  const ALL_DEPARTMENTS = ["Cardiology", "Orthopaedics", "Ophthalmology", "Dermatology", "Pediatrics", "General Medicine"];
  
  // Filter tokens based on selected department
  const filteredTokens = selectedDept 
    ? tokens.filter(t => t.department === selectedDept)
    : tokens;

  return (
    <main className="min-h-screen p-10 bg-slate-900 text-slate-50">
      <div className="flex justify-between items-center mb-10 border-b border-slate-700 pb-6">
        <div>
          <h1 className="text-4xl font-bold flex items-center gap-4">
            <Activity className="text-sky-500 w-10 h-10" /> 
            RAYA Admin Dashboard
          </h1>
          <p className="text-slate-400 mt-2">Live view of local RAYA and ABHA interactions</p>
        </div>
        <button 
          onClick={fetchData}
          className="bg-slate-800 hover:bg-slate-700 p-3 rounded-full transition-colors flex items-center"
          title="Refresh Data"
        >
          <RefreshCw className={`w-6 h-6 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-10">
        
        {/* Token Queue */}
        <div className="glass-panel p-6 rounded-3xl border-t-4 border-t-sky-500 flex flex-col max-h-[800px] overflow-hidden">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 shrink-0">
            <h2 className="text-2xl font-semibold flex items-center gap-3">
              <List className="text-sky-400" /> Live OPD Queue
            </h2>
            
            {/* Department Filter Buttons */}
            <div className="flex flex-wrap gap-2 items-center">
              <Filter className="w-4 h-4 text-slate-400 mr-2" />
              <button
                onClick={() => setSelectedDept(null)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  selectedDept === null 
                  ? "bg-sky-500 text-white" 
                  : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                }`}
              >
                All
              </button>
              {ALL_DEPARTMENTS.map(dept => (
                <button
                  key={dept}
                  onClick={() => setSelectedDept(dept)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    selectedDept === dept 
                    ? "bg-sky-500 text-white" 
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                  }`}
                >
                  {dept}
                </button>
              ))}
            </div>
          </div>
          
          <div className="overflow-y-auto flex-1 pr-2">
            {filteredTokens.length === 0 ? (
              <div className="text-center text-slate-500 py-10">No active tokens in queue.</div>
            ) : (
              <table className="w-full text-left">
                <thead>
                  <tr className="text-slate-400 text-sm border-b border-slate-700">
                    <th className="pb-3 font-medium">Token</th>
                    <th className="pb-3 font-medium">Patient</th>
                    <th className="pb-3 font-medium">Department</th>
                    <th className="pb-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTokens.map((t: any, idx: number) => (
                    <motion.tr 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      key={t.token_number} 
                      className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors"
                    >
                      <td className="py-4 font-mono text-sky-400">{t.token_number}</td>
                      <td className="py-4 font-medium">{t.patient_name}</td>
                      <td className="py-4 text-slate-400">{t.department}</td>
                      <td className="py-4 text-right">
                        <div className="flex justify-end gap-2">
                          {t.status !== 'COMPLETED' && (
                            <button 
                              onClick={() => handleCompleteToken(t.token_number)}
                              className="px-3 py-2 bg-green-500/10 text-green-400 hover:bg-green-500/20 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
                              title="End Meeting & Remove from Queue"
                            >
                              <CheckCircle className="w-4 h-4" /> End Meeting
                            </button>
                          )}
                          <button 
                            onClick={() => handleDeleteToken(t.token_number)}
                            className="p-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                            title="Delete Token"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Local RAYA Users (Biometric DB) */}
        <div className="glass-panel p-6 rounded-3xl border-t-4 border-t-teal-500 flex flex-col max-h-[800px] overflow-hidden">
          <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3 shrink-0">
            <Users className="text-teal-400" /> Local Enrolled Profiles (RAYA DB)
          </h2>
          
          <div className="overflow-y-auto flex-1 pr-2">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-700 text-slate-400">
                  <th className="pb-3 font-medium">ID</th>
                  <th className="pb-3 font-medium">Full Name</th>
                  <th className="pb-3 font-medium">Linked ABHA</th>
                  <th className="pb-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-slate-500">No locally enrolled users.</td>
                  </tr>
                ) : (
                  users.map((u, idx) => (
                    <motion.tr 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      key={u.id} 
                      className="border-b border-slate-800/50 hover:bg-slate-800/50 transition-colors"
                    >
                      <td className="py-4 text-slate-400">#{u.id}</td>
                      <td className="py-4 font-medium">{u.full_name}</td>
                      <td className="py-4 font-mono text-teal-400">{u.abha_number || "Unlinked"}</td>
                      <td className="py-4 text-right">
                        <button 
                          onClick={() => handleDeleteUser(u.id)}
                          className="p-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                          title="Delete User"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </main>
  );
}
