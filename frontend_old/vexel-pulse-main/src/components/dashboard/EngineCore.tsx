import { Cpu } from "lucide-react";
import { motion } from "framer-motion";

interface EngineCoreProps {
  isActive: boolean;
}

const EngineCore = ({ isActive }: EngineCoreProps) => {
  return (
    <div className="flex flex-col items-center justify-center py-8 gap-4">
      <div className="relative">
        {/* Outer pulse rings */}
        {isActive && (
          <>
            <div className="absolute inset-0 rounded-full bg-primary/20 pulse-ring" />
            <div className="absolute inset-0 rounded-full bg-primary/10 pulse-ring" style={{ animationDelay: "1s" }} />
          </>
        )}
        {/* Core */}
        <motion.div
          animate={isActive ? { rotate: 360 } : { rotate: 0 }}
          transition={isActive ? { duration: 8, repeat: Infinity, ease: "linear" } : {}}
          className={`relative z-10 p-6 rounded-full border-2 transition-all duration-500 ${
            isActive
              ? "border-primary/60 bg-primary/10 glow-blue"
              : "border-border bg-muted/30"
          }`}
        >
          <Cpu
            className={`w-10 h-10 transition-colors duration-500 ${
              isActive ? "text-primary" : "text-muted-foreground"
            }`}
          />
        </motion.div>
        {/* Breathing glow behind */}
        {isActive && (
          <div className="absolute inset-[-12px] rounded-full bg-primary/20 breathe -z-10" />
        )}
      </div>
      <div className="text-center">
        <p className="font-display font-semibold text-foreground">
          {isActive ? "Engine Running" : "Engine Idle"}
        </p>
        <p className="text-xs text-muted-foreground font-body mt-1">
          {isActive ? "Processing warmup tasks..." : "Awaiting start command"}
        </p>
      </div>
    </div>
  );
};

export default EngineCore;
