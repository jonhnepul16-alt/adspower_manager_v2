import { useState } from "react";
import { motion } from "framer-motion";
import { Zap, Timer, Flame } from "lucide-react";

const strategies = [
  { id: "1", label: "Rápido", duration: "~15 min", icon: Zap },
  { id: "2", label: "Padrão", duration: "~45 min", icon: Timer },
  { id: "3", label: "Intenso", duration: "~2h", icon: Flame },
];

interface StrategySelectorProps {
  value: string;
  onChange: (value: string) => void;
}

const StrategySelector = ({ value, onChange }: StrategySelectorProps) => {


  return (
    <div className="flex gap-2">
      {strategies.map((s) => {
        const isActive = value === s.id;
        return (
          <button
            key={s.id}
            onClick={() => onChange(s.id)}
            className={`relative flex-1 flex flex-col items-center gap-1.5 py-4 px-3 rounded-2xl border transition-all duration-300 font-body text-sm ${
              isActive
                ? "border-primary/50 bg-primary/10 text-foreground glow-pulse"
                : "border-border bg-muted/30 text-muted-foreground hover:border-muted-foreground/30 hover:bg-muted/50"
            }`}
          >
            {isActive && (
              <motion.div
                layoutId="strategy-glow"
                className="absolute inset-0 rounded-2xl border border-primary/40"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <s.icon className={`w-5 h-5 ${isActive ? "text-primary" : ""}`} />
            <span className="font-display font-semibold">{s.label}</span>
            <span className="text-xs text-muted-foreground">{s.duration}</span>
          </button>
        );
      })}
    </div>
  );
};

export default StrategySelector;
