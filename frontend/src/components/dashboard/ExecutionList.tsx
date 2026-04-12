import { motion } from "framer-motion";
import { Zap, Clock } from "lucide-react";
import { useState, useEffect } from "react";

interface Props {
  profiles: string[];
  currentProfile: string | null;
  results: Record<string, any>;
  currentTaskStart?: number;
  currentTaskDuration?: number;
}

const formatTime = (seconds: number) => {
  if (seconds <= 0) return "00:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

const ExecutionList = ({ profiles, currentProfile, results, currentTaskStart, currentTaskDuration }: Props) => {
  const [now, setNow] = useState(Date.now() / 1000);

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now() / 1000), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-4">
      {profiles.map((pid, i) => {
        const isCurrent = pid === currentProfile;
        const result = results[pid] || {};
        const isCompleted = !isCurrent && result.ok && (result.ciclos > 0);
        const interactions = (result.curtidas_feed || 0) + (result.reacoes_dadas || 0) + (result.comentarios_feitos || 0) + (result.reels_assistidos || 0);
        
        // Calculate remaining time
        let timeLeft = 0;
        if (isCurrent && currentTaskStart && currentTaskDuration) {
          const elapsed = now - currentTaskStart;
          timeLeft = Math.max(0, currentTaskDuration - elapsed);
        }

        return (
          <div key={pid} className="flex items-center justify-between p-4 bg-white/[0.02] border border-white/[0.05] rounded-2xl hover:bg-white/[0.05] transition-all">
            <div className="flex items-center gap-4">
              <div className={`p-2.5 rounded-full ${isCurrent ? "bg-primary/20 text-primary border border-primary/30 shadow-[0_0_10px_rgba(240,90,40,0.2)]" : "bg-white/5 text-muted-foreground"}`}>
                <Zap className={`w-4 h-4 ${isCurrent ? "animate-pulse" : ""}`} />
              </div>
              <div className="flex flex-col">
                <span className="text-[12px] font-bold text-foreground">Perfil_{String(i + 1).padStart(2, '0')}</span>
                <span className="text-[10px] text-muted-foreground tracking-wider">{pid}</span>
              </div>
            </div>

            <div className="flex items-center gap-12">
               <div className="flex flex-col items-end gap-1">
                  <span className={`text-[9px] font-black uppercase tracking-[0.1em] ${isCurrent ? "text-primary" : isCompleted ? "text-emerald-500" : "text-muted-foreground/40"}`}>
                    {isCurrent ? "AQUECENDO" : isCompleted ? "CONCLUÍDO" : "NA FILA"}
                  </span>
                  <div className="w-32 h-1 bg-white/5 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: isCurrent ? "60%" : isCompleted ? "100%" : "0%" }}
                      className={`h-full ${isCurrent ? "bg-primary" : isCompleted ? "bg-emerald-500" : "bg-muted"}`}
                    />
                  </div>
               </div>
               
               <div className="flex flex-col items-end min-w-[60px]">
                  {isCurrent ? (
                    <div className="flex items-center gap-1 text-primary">
                      <Clock className="w-3 h-3 animate-pulse" />
                      <span className="font-mono text-xs font-black">{formatTime(timeLeft)}</span>
                    </div>
                  ) : (
                    <span className="font-mono text-sm font-bold text-foreground/80">{interactions}</span>
                  )}
                  {isCurrent && (
                    <span className="text-[8px] text-white/20 font-bold uppercase tracking-widest mt-0.5">restante</span>
                  )}
               </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ExecutionList;
