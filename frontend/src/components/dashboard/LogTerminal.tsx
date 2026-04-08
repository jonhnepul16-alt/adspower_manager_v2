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
    <div className="flex-1 bg-[#111111] rounded-xl border border-border/20 p-4 font-mono text-[10px] overflow-hidden flex flex-col relative min-h-[150px]">
      <div className="absolute top-0 inset-x-0 h-4 bg-gradient-to-b from-[#111111] to-transparent z-10" />
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-2 pb-4 pt-2"
      >
        {liveLogs.length === 0 ? (
          <div className="flex flex-col items-center gap-2 text-muted-foreground/30 h-full justify-center">
            <div className="p-3 rounded-full bg-card/50 border border-border/20 mb-2">
              <Terminal className="w-5 h-5 text-primary/40" />
            </div>
            <span className="uppercase tracking-[0.2em] text-[9px] font-black text-primary/40 text-center">Sistema Sincronizado</span>
            <span className="text-[8px] font-medium opacity-40 text-center">Aguardando telemetria da nuvem...</span>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {liveLogs.map((log, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                className="flex gap-2"
              >
                <span className="text-primary/70 shrink-0 select-none">
                  ❯
                </span>
                <span className="text-muted-foreground break-all">
                  {log}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
      <div className="absolute bottom-0 inset-x-0 h-8 bg-gradient-to-t from-[#111111] to-transparent z-10" />
      
      {isActive && (
        <div className="absolute bottom-3 left-4 flex gap-2 w-full z-20 bg-[#111111]">
          <span className="text-primary/70">❯</span>
          <span className="w-2 h-3 bg-primary/70 animate-pulse mt-0.5" />
        </div>
      )}
    </div>
  );
};

export default LogTerminal;
