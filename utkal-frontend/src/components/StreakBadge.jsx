import React from "react";
import { Flame, Star } from "lucide-react";

export default function StreakBadge({ days, earned = false, year = 2026 }) {
  const isLarge = days >= 100;
  
  return (
    <div className={`relative group flex flex-col items-center ${earned ? "opacity-100" : "opacity-40 grayscale"}`}>
      <div className={`relative flex items-center justify-center transition-transform group-hover:scale-110 duration-500`}>
        {/* Hexagonal Background Layer */}
        <div className={`absolute inset-0 bg-gradient-to-br ${days >= 365 ? "from-yellow-400 to-orange-600" : days >= 100 ? "from-blue-500 to-indigo-700" : "from-orange-400 to-red-600"} rounded-3xl rotate-45 shadow-xl`}></div>
        <div className="absolute inset-[4px] bg-slate-900 rounded-[1.2rem] rotate-45"></div>
        
        {/* Inner Content Container */}
        <div className="relative w-24 h-24 flex flex-col items-center justify-center z-10 text-white">
          <div className="flex items-center gap-0.5 mb-0.5">
             <span className="text-2xl font-black tracking-tighter">{days}</span>
          </div>
          <span className="text-[10px] font-black uppercase tracking-[0.15em] opacity-80">Days</span>
          
          {/* Decorative Elements */}
          <div className="absolute top-1 right-1">
             <Star className="w-2 h-2 text-yellow-400 fill-yellow-400 animate-pulse" />
          </div>
        </div>

        {/* Outer Glow for Earned Badges */}
        {earned && (
           <div className={`absolute -inset-2 bg-gradient-to-r ${days >= 365 ? "from-yellow-500/30 to-transparent" : "from-blue-500/30 to-transparent"} rounded-full blur-xl -z-10 animate-pulse`}></div>
        )}
      </div>

      <div className="mt-4 text-center">
        <h4 className="text-sm font-bold text-slate-800">{days} Days Badge</h4>
        <p className="text-[10px] text-slate-500 font-medium uppercase tracking-widest">{year}</p>
      </div>

      {!earned && (
          <div className="absolute top-0 right-0 bg-slate-800 text-white text-[8px] font-bold px-1.5 py-0.5 rounded-full z-20">
             Locked
          </div>
      )}
    </div>
  );
}
