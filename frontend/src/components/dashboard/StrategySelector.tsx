import { Target, Zap, Lock } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";

interface Props {
  value: string;
  onChange: (val: string) => void;
  plan?: string;
}

const StrategySelector = ({ value, onChange, plan }: Props) => {
  const modes = [
    {
      id: "1",
      name: "Orgânico",
      icon: Target,
      isPremium: false
    },
    {
      id: "2",
      name: "Agressivo",
      icon: Zap,
      isPremium: true
    },
  ];

  return (
    <div className="segmented-control p-1 bg-white/[0.02] border border-white/[0.05] rounded-xl flex gap-1">
      {modes.map((mode) => {
        const isActive = value === mode.id;
        const isLocked = mode.isPremium && plan !== "SCALE" && plan !== "TEAM";

        return (
          <button
            key={mode.id}
            onClick={() => {
              if (isLocked) {
                toast.info("Este modo é exclusivo para planos Premium (Scale/Team).", {
                  description: "Faça o upgrade para desbloquear funções premium."
                });
                return;
              }
              onChange(mode.id);
            }}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all relative overflow-hidden
              ${isActive 
                ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" 
                : "text-muted-foreground hover:bg-white/5"
              }
              ${isLocked ? "opacity-60 grayscale-[0.5]" : ""}
            `}
          >
            {isLocked ? (
              <Lock className="w-3 h-3 text-white/40" />
            ) : (
              <mode.icon className={`w-3.5 h-3.5 ${isActive ? "text-primary-foreground" : "text-primary/60"}`} />
            )}
            <span>{mode.name}</span>
            {isLocked && (
              <span className="absolute -right-4 -top-1 bg-primary/20 text-primary text-[6px] font-black px-4 py-1.5 rotate-45 border-b border-primary/30">
                SCALE
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};

export default StrategySelector;
