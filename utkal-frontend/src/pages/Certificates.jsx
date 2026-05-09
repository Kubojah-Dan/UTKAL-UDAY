import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { Trophy, Award, Download, Printer, ChevronLeft, ShieldCheck, X } from "lucide-react";
import { useNavigate } from "react-router-dom";

function CertificateModal({ cert, onClose }) {
  if (!cert) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-md animate-in fade-in duration-300 no-print">
      <div className="bg-white rounded-[2.5rem] shadow-2xl max-w-5xl w-full max-h-[95vh] overflow-y-auto relative no-print">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-2 hover:bg-slate-100 rounded-full transition-colors z-10 no-print"
        >
          <X className="w-6 h-6 text-slate-400" />
        </button>

        <div id="certificate-print-area" className="p-12 md:p-16 bg-white print:p-0">
          <div className="border-[12px] border-double border-slate-200 p-8 md:p-12 relative overflow-hidden bg-slate-50/30">
            {/* Logo and Header */}
            <div className="flex flex-col items-center mb-12 relative z-10">
              <img src="/utkal-uday-logo.svg" alt="Utkal Uday" className="w-24 h-24 mb-4" />
              <h1 className="text-4xl font-serif font-bold text-slate-800 tracking-tight">UTKAL UDAY</h1>
              <div className="w-24 h-1 bg-brand my-4"></div>
              <p className="text-slate-500 uppercase tracking-[0.2em] font-bold text-xs">Achievement Certificate</p>
            </div>

            {/* Content */}
            <div className="text-center space-y-6 relative z-10">
              <p className="text-xl italic font-serif text-slate-600">This is to certify that</p>
              <h2 className="text-5xl font-serif font-black text-slate-900 py-2 border-b-2 border-slate-100 inline-block px-12">
                {cert.student_name}
              </h2>
              <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
                has demonstrated exceptional academic performance and dedication on the Utkal Uday AI Learning Platform.
                This award is presented for achieving:
              </p>
              <div className="bg-brand/5 border border-brand/10 py-6 px-10 rounded-2xl inline-block">
                <span className="text-2xl font-bold text-brand">{cert.achievement_title}</span>
                <p className="text-slate-500 text-sm mt-1">{cert.achievement_detail}</p>
              </div>
            </div>

            {/* Footer */}
            <div className="mt-16 flex justify-between items-end relative z-10">
              <div className="text-center">
                <div className="w-48 border-b border-slate-300 pb-2 mb-2">
                  <span className="font-serif italic text-slate-700">Digital Verification</span>
                </div>
                <p className="text-[10px] text-slate-400 font-mono">{cert.id}</p>
              </div>
              <div className="flex flex-col items-center">
                <ShieldCheck className="w-16 h-16 text-brand/30 mb-2" />
                <p className="text-[10px] text-slate-400 font-mono uppercase tracking-widest">Utkal Uday AI Certified</p>
              </div>
              <div className="text-center">
                <div className="w-48 border-b border-slate-300 pb-2 mb-2">
                  <span className="text-slate-700 font-bold">{new Date(cert.date).toLocaleDateString()}</span>
                </div>
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Date of Issue</p>
              </div>
            </div>

            {/* Background elements (non-printing maybe? or watermark) */}
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-brand/5 rounded-full blur-3xl"></div>
            <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-brand/5 rounded-full blur-3xl"></div>
          </div>
        </div>

        <div className="p-6 bg-slate-50 border-t flex justify-end gap-3 no-print">
          <button onClick={onClose} className="px-6 py-2 rounded-xl text-slate-600 hover:bg-slate-200 transition-colors">
            Close
          </button>
          <button onClick={handlePrint} className="btn-primary flex items-center gap-2">
            <Printer className="w-4 h-4" /> Print / Save as PDF
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Certificates() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [certs, setCerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCert, setActiveCert] = useState(null);

  useEffect(() => {
    const fetchCerts = async () => {
      try {
        // Logic: Check if user is in Hall of Fame or has streaks
        const [lbRes, hofRes] = await Promise.all([
          api.get("/leaderboard/my-rank", { params: { scope: "state", grade: user.class_grade } }),
          api.get("/leaderboard/hall-of-fame", { params: { grade: user.class_grade } })
        ]);

        const myHallOfFame = hofRes.data?.hall_of_fame || [];
        const isHof = myHallOfFame.some(h => h.student_id === user.id);
        const myRank = lbRes.data;

        const earned = [];

        if (isHof) {
          earned.push({
            id: `HOF-${user.id}-2026`,
            type: "hall-of-fame",
            student_name: user.name,
            achievement_title: "Hall of Fame - Class of 2026",
            achievement_detail: `Achieved Top 10 rank in Grade ${user.class_grade} among all schools.`,
            date: new Date().toISOString()
          });
        }

        if (myRank.rank === 1) {
          earned.push({
            id: `TOP1-${user.id}-${Date.now()}`,
            type: "rank-1",
            student_name: user.name,
            achievement_title: "State Champion - Rank #1",
            achievement_detail: `Highest academic performance in Grade ${user.class_grade} across the state.`,
            date: new Date().toISOString()
          });
        }

        // Add a "Welcome" certificate for everyone just for demo if they have some XP
        if (user.xp_earned > 1000 || earned.length === 0) {
             earned.push({
                id: `GEN-${user.id}-START`,
                type: "milestone",
                student_name: user.name,
                achievement_title: "Learning Milestone",
                achievement_detail: `For active participation and consistent learning progress in Grade ${user.class_grade}.`,
                date: new Date().toISOString()
             });
        }

        setCerts(earned);
      } catch (err) {
        console.error("Failed to fetch certifications", err);
      } finally {
        setLoading(false);
      }
    };

    fetchCerts();
  }, [user]);

  return (
    <div className="container py-8 max-w-5xl">
      <div className="flex items-center gap-4 mb-8">
        <button 
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-slate-100 rounded-full transition-colors no-print"
        >
          <ChevronLeft className="w-6 h-6" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-slate-900">My Certificates</h1>
          <p className="text-slate-500">Official recognition for your academic excellence.</p>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-6 md:grid-cols-2">
            {[1, 2].map(i => <div key={i} className="h-48 bg-slate-100 animate-pulse rounded-3xl"></div>)}
        </div>
      ) : certs.length === 0 ? (
        <div className="panel flex flex-col items-center justify-center py-20 text-center">
          <Award className="w-16 h-16 text-slate-200 mb-4" />
          <h2 className="text-xl font-bold text-slate-700">No Certificates Yet</h2>
          <p className="text-slate-500 max-w-xs mt-2">
            Keep practicing and climb the leaderboard to unlock official Utkal Uday certificates!
          </p>
          <button 
            onClick={() => navigate("/quest")}
            className="btn-primary mt-6"
          >
            Start Practicing
          </button>
        </div>
      ) : (
        <div className="grid gap-8 md:grid-cols-2">
          {certs.map(cert => (
            <div 
              key={cert.id} 
              className="bg-white rounded-[2rem] border border-slate-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all p-8 flex flex-col items-center text-center group cursor-pointer"
              onClick={() => setActiveCert(cert)}
            >
              <div className="w-20 h-20 bg-brand/5 rounded-full flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Trophy className="w-10 h-10 text-brand" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">{cert.achievement_title}</h3>
              <p className="text-sm text-slate-500 mb-6 flex-grow">{cert.achievement_detail}</p>
              <div className="flex items-center gap-3 mt-auto w-full">
                <button className="flex-1 bg-slate-50 hover:bg-slate-100 text-slate-600 font-bold py-3 rounded-2xl flex items-center justify-center gap-2 transition-colors">
                   View Certificate
                </button>
                <button className="w-12 h-12 bg-brand/10 hover:bg-brand text-brand hover:text-white rounded-2xl flex items-center justify-center transition-all">
                  <Download className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info Section */}
      <div className="mt-16 p-8 bg-brand/5 rounded-[2.5rem] border border-brand/10">
        <div className="flex flex-col md:flex-row gap-8 items-center">
            <div className="w-24 h-24 bg-brand rounded-3xl flex items-center justify-center shrink-0 shadow-lg shadow-brand/20">
                <ShieldCheck className="w-12 h-12 text-white" />
            </div>
            <div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Academic Validation</h2>
                <p className="text-slate-600 leading-relaxed">
                    Certificates issued by Utkal Uday are backed by real-time learning analytics. 
                    They recognize top performance in regional competitive leaderboards and consistent academic progress.
                    These can be shared with teachers or included in your student portfolio.
                </p>
            </div>
        </div>
      </div>

      <CertificateModal 
        cert={activeCert} 
        onClose={() => setActiveCert(null)} 
      />

      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          .no-print { display: none !important; }
          body { background: white !important; }
          .container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
          #certificate-print-area { display: block !important; }
          .app-shell { background: white !important; }
          header, footer, .sync-pill, .nav { display: none !important; }
        }
      `}} />
    </div>
  );
}
