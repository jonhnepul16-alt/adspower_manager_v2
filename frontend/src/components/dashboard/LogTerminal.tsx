import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

interface LogEntry {
  id: number;
  type: "success" | "error" | "info" | "scheduler";
  message: string;
  time: string;
}

const sampleLogs: LogEntry[] = [
  { id: 1, type: "info", message: "Initializing browser profiles...", time: "12:04:01" },
  { id: 2, type: "success", message: "Profile #1 loaded successfully", time: "12:04:03" },
  { id: 3, type: "success", message: "Profile #2 loaded successfully", time: "12:04:04" },
  { id: 4, type: "info", message: "Starting warmup sequence [Padrão]", time: "12:04:05" },
  { id: 5, type: "success", message: "Like action completed — Post #4821", time: "12:04:12" },
  { id: 6, type: "success", message: "Reel watch completed — 32s duration", time: "12:04:45" },
  { id: 7, type: "error", message: "Rate limit warning — cooldown 15s", time: "12:05:00" },
  { id: 8, type: "info", message: "Resuming actions after cooldown", time: "12:05:15" },
  { id: 9, type: "success", message: "Status published — Profile #1", time: "12:05:22" },
  { id: 10, type: "success", message: "Like action completed — Post #4822", time: "12:05:30" },
];

const typeColors: Record<string, string> = {
  success: "text-emerald-400",
  error: "text-red-400",
  info: "text-primary",
  scheduler: "text-indigo-400",
};

const typePrefix: Record<string, string> = {
  success: "✓",
  error: "✗",
  info: "→",
  scheduler: "⏰",
};

interface LogTerminalProps {
  isActive: boolean;
  liveLogs: string[];
}

const LogTerminal = ({ isActive, liveLogs }: LogTerminalProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const parsedLogs = liveLogs.map((line, i) => {
    const timeMatch = line.match(/\[(.*?)\]/);
    const time = timeMatch ? timeMatch[1] : new Date().toLocaleTimeString();
    let type: "info" | "success" | "error" | "scheduler" = "info";
    
    if (line.includes("[SCHEDULER]")) {
      type = "scheduler";
    } else if (line.includes("✓")) {
      type = "success";
    } else if (line.includes("✗") || line.toLowerCase().includes("erro")) {
      type = "error";
    }
    
    return {
      id: i,
      time,
      type,
      message: line.replace(/\[.*?\]\s*/g, "").replace("[SCHEDULER]", "").trim()
    };
  });


  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [parsedLogs]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-500/60" />
            <span className="w-3 h-3 rounded-full bg-yellow-500/60" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/60" />
          </div>
          <span className="text-xs text-muted-foreground font-mono ml-2">log_output.sh</span>
        </div>
        {!isActive && (
          <span className="text-xs text-muted-foreground ghost-pulse font-mono">idle</span>
        )}
      </div>
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto max-h-[320px] space-y-1 pr-2 scrollbar-thin"
      >
        {parsedLogs.map((log, i) => (
          <motion.div
            key={log.id + "-" + i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
            className="flex gap-3 font-mono text-xs leading-relaxed"
          >
            <span className="text-muted-foreground/50 select-none w-6 text-right shrink-0">
              {(i + 1).toString().padStart(2, "0")}
            </span>
            <span className="text-muted-foreground/40 shrink-0">{log.time}</span>
            <span className={typeColors[log.type]}>{typePrefix[log.type]}</span>
            <span className="text-foreground/80">{log.message}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default LogTerminal;
