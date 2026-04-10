import { motion } from "framer-motion";
import { Zap } from "lucide-react";

interface Props {
  profiles: string[];
  currentProfile: string | null;
  results: Record<string, any>;
}

const ExecutionList = ({ profiles, currentProfile, results }: Props) => {
  return (
    <div className="space-y-4">
      {profiles.map((pid, i) => {
        const isCurrent = pid === currentProfile;
        const result = results[pid] || {};
        const isCompleted = !isCurrent && result.ok && (result.ciclos > 0);
        const interactions = (result.curtidas_feed || 0) + (result.reacoes_dadas || 0) + (result.comentarios_feitos || 0) + (result.reels_assistidos || 0);
        
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
               
               <div className="w-10 text-right">
                  <span className="font-mono text-sm font-bold text-foreground/80">{interactions}</span>
               </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ExecutionList;
