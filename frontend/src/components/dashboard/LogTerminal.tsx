import { useEffect, useRef } from "react";
import { Terminal } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface LogTerminalProps {
  isActive: boolean;
  liveLogs: string[];
}

const LogTerminal = ({ isActive, liveLogs }: LogTerminalProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [liveLogs]);

  return (
    <div className="flex flex-col h-full">
      {/* Bloco Atividade em Tempo Real Header */}
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-primary animate-pulse" />
          <h2 className="font-display font-bold text-xs uppercase tracking-[0.2em] text-foreground">
            Atividade em Tempo Real
          </h2>
        </div>
        <div className="flex gap-1">
          <div className="w-2 h-2 rounded-full bg-red-500/50" />
          <div className="w-2 h-2 rounded-full bg-amber-500/50" />
          <div className="w-2 h-2 rounded-full bg-emerald-500/50" />
        </div>
      </div>

      <div className="flex-1 bg-black rounded-xl border border-border/10 p-4 font-mono text-[10px] overflow-hidden flex flex-col relative min-h-[180px] shadow-2xl">
        <div className="absolute top-0 inset-x-0 h-4 bg-gradient-to-b from-black to-transparent z-10" />
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-1.5 pb-4 pt-2"
        >
          {liveLogs.length === 0 ? (
            <div className="flex flex-col items-center gap-2 text-primary/10 h-full justify-center">
              <Terminal className="w-5 h-5 opacity-20" />
              <span className="uppercase tracking-[0.3em] text-[8px] font-black">Aguardando Telemetria...</span>
            </div>
          ) : (
            <AnimatePresence initial={false}>
              {liveLogs.map((log, i) => {
                // Lógica de Cores Realista: Verde para sucesso, Amarelo para processo, Branco para o resto
                const isSuccess = log.includes("✓") || log.includes("OK") || log.includes("concluído");
                const isProcess = log.includes("▶") || log.includes("⏱") || log.includes("...") || log.includes("focando");
                
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.15 }}
                    className="flex gap-2 items-start leading-relaxed"
                  >
                    <span className="text-primary/40 shrink-0 select-none mt-0.5">
                      [{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
                    </span>
                    <span className={`break-all ${
                      isSuccess ? "text-emerald-400 font-bold" : 
                      isProcess ? "text-amber-400" : 
                      "text-foreground/80"
                    }`}>
                      {log.trim()}
                    </span>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          )}
        </div>
        <div className="absolute bottom-0 inset-x-0 h-8 bg-gradient-to-t from-black to-transparent z-10 pointer-events-none" />
        
        {isActive && (
          <div className="absolute bottom-3 left-4 flex gap-2 z-20">
            <span className="text-primary/70 animate-bounce">❯</span>
            <div className="flex gap-0.5 mt-0.5">
              <span className="w-1.5 h-3 bg-primary/80 animate-[pulse_1s_infinite]" />
              <span className="w-1.5 h-3 bg-primary/40 animate-[pulse_1.5s_infinite]" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LogTerminal;
