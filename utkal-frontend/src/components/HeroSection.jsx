import React from "react";
import { Button } from "@/components/ui/button";
import { Play, Smartphone, WifiOff } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function HeroSection() {
    const navigate = useNavigate();
    const { user } = useAuth();

    const handleStartQuest = () => {
        if (!user) navigate("/login");
        else if (user.role === "teacher") navigate("/teacher");
        else navigate("/home");
    };

    return (
        <section className="relative overflow-hidden bg-gradient-hero py-16 md:py-24">
            {/* Background decoration */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-20 right-10 w-64 h-64 bg-accent/10 rounded-full blur-3xl" />
                <div className="absolute bottom-20 left-10 w-48 h-48 bg-primary/10 rounded-full blur-3xl" />
            </div>

            <div className="container relative">
                <div className="grid lg:grid-cols-2 gap-12 items-center">
                    {/* Content */}
                    <div className="animate-fade-in">

                        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight mb-6">
                            <span className="text-gradient-teal">Utkal Quest:</span>
                            <br />
                            <span className="text-foreground">AI-Driven Gamified</span>
                            <br />
                            <span className="text-gradient-sunrise">Mastery</span>
                        </h1>

                        <p className="text-lg text-muted-foreground mb-8 max-w-lg">
                            Empowering rural students in Odisha with offline-first, gamified STEM learning.
                            Build mathematical intuition through quests, not just formulas.
                        </p>

                        <div className="flex flex-wrap gap-4 mb-8">
                            <Button size="lg" className="bg-gradient-teal hover:opacity-90 shadow-soft" onClick={handleStartQuest}>
                                <Play className="h-5 w-5 mr-2" />
                                Start Your Quest
                            </Button>
                            <Button size="lg" variant="outline" className="border-primary/30 hover:bg-primary/5" onClick={() => navigate("/download-app")}>
                                <Smartphone className="h-5 w-5 mr-2" />
                                Download App
                            </Button>
                        </div>

                        {/* Key Features Pills */}
                        <div className="flex flex-wrap gap-3">
                            <div className="flex items-center gap-2 bg-card px-4 py-2 rounded-full shadow-card text-sm">
                                <WifiOff className="h-4 w-4 text-primary" />
                                <span className="text-muted-foreground">Works Offline</span>
                            </div>
                            <div className="flex items-center gap-2 bg-card px-4 py-2 rounded-full shadow-card text-sm">
                                <span className="text-accent">🏆</span>
                                <span className="text-muted-foreground">Gamified Learning</span>
                            </div>
                            <div className="flex items-center gap-2 bg-card px-4 py-2 rounded-full shadow-card text-sm">
                                <span className="text-primary">🧠</span>
                                <span className="text-muted-foreground">AI-Powered</span>
                            </div>
                        </div>
                    </div>

                    {/* Visual - Mastery Galaxy (Dynamic & Colorful) */}
                    <div className="relative h-[500px] flex items-center justify-center animate-fade-in">
                        {/* Central Hub - The "AI Brain" */}
                        <div className="relative z-10 w-32 h-32 bg-white rounded-full shadow-elevated flex items-center justify-center p-4 group cursor-pointer hover:scale-110 transition-transform duration-700">
                             <div className="absolute inset-0 bg-gradient-teal rounded-full opacity-20 group-hover:opacity-40 animate-pulse"></div>
                             <img src="/utkal-uday-logo.svg" alt="Utkal Uday" className="w-full h-full relative z-10 animate-float" />
                        </div>

                        {/* Orbiting Subject Mastery Cards */}
                        <div className="absolute inset-0 z-0">
                            {/* Mathematics - Orbit 1 */}
                            <div className="absolute top-10 right-20 w-48 bg-white/80 backdrop-blur-md rounded-2xl p-4 shadow-soft border border-blue-100 animate-float-slow group hover:z-30 cursor-pointer" style={{ animationDelay: "0s" }}>
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-xs font-bold text-blue-600 uppercase">Mathematics</span>
                                    <span className="text-sm font-black text-slate-800">82%</span>
                                </div>
                                <div className="h-1.5 bg-blue-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500 w-[82%] rounded-full shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
                                </div>
                                <div className="mt-2 flex gap-1">
                                    {[1,2,3].map(i => <div key={i} className="w-1.5 h-1.5 rounded-full bg-blue-400 opacity-60"></div>)}
                                </div>
                            </div>

                            {/* Science - Orbit 2 */}
                            <div className="absolute bottom-20 left-10 w-44 bg-white/80 backdrop-blur-md rounded-2xl p-4 shadow-soft border border-emerald-100 animate-float-slow group hover:z-30 cursor-pointer" style={{ animationDelay: "1.5s" }}>
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-xs font-bold text-emerald-600 uppercase">Science</span>
                                    <span className="text-sm font-black text-slate-800">65%</span>
                                </div>
                                <div className="h-1.5 bg-emerald-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-emerald-500 w-[65%] rounded-full shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                                </div>
                                <div className="mt-2 flex gap-1">
                                    <div className="px-2 py-0.5 bg-emerald-100 text-[8px] font-bold text-emerald-700 rounded-full uppercase tracking-tighter">Rising Star</div>
                                </div>
                            </div>

                            {/* English - Orbit 3 */}
                            <div className="absolute top-1/2 -right-4 w-40 bg-white/80 backdrop-blur-md rounded-2xl p-4 shadow-soft border border-purple-100 animate-float-slow group hover:z-30 cursor-pointer" style={{ animationDelay: "3s" }}>
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-xs font-bold text-purple-600 uppercase">English</span>
                                    <span className="text-sm font-black text-slate-800">91%</span>
                                </div>
                                <div className="h-1.5 bg-purple-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-purple-500 w-[91%] rounded-full shadow-[0_0_8px_rgba(139,92,246,0.5)]"></div>
                                </div>
                            </div>

                            {/* Social Science - Orbit 4 */}
                            <div className="absolute top-20 left-4 w-36 bg-white/80 backdrop-blur-md rounded-2xl p-4 shadow-soft border border-orange-100 animate-float-slow group hover:z-30 cursor-pointer" style={{ animationDelay: "4.5s" }}>
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-xs font-bold text-orange-600 uppercase">Social</span>
                                    <span className="text-sm font-black text-slate-800">44%</span>
                                </div>
                                <div className="h-1.5 bg-orange-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-orange-500 w-[44%] rounded-full"></div>
                                </div>
                            </div>
                        </div>

                        {/* Particle Effects (Floating Orbs) */}
                        <div className="absolute top-1/4 left-1/3 w-3 h-3 bg-blue-400 rounded-full blur-sm animate-pulse"></div>
                        <div className="absolute bottom-1/3 right-1/4 w-2 h-2 bg-purple-400 rounded-full blur-sm animate-pulse duration-1000"></div>
                        <div className="absolute top-1/2 left-1/4 w-4 h-4 bg-orange-300 rounded-full blur-md animate-pulse duration-700"></div>
                    </div>
                </div>
            </div>
            
            {/* Added extra CSS for the slow float and pulse */}
            <style dangerouslySetInnerHTML={{ __html: `
                @keyframes float-slow {
                    0%, 100% { transform: translateY(0) scale(1); }
                    50% { transform: translateY(-20px) scale(1.02); }
                }
                .animate-float-slow { animation: float-slow 6s ease-in-out infinite; }
            `}} />
        </section>
    );
}
