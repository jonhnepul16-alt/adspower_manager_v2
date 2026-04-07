import { Target, Zap } from "lucide-react";
import { motion } from "framer-motion";

interface Props {
  value: string;
  onChange: (val: string) => void;
}

const StrategySelector = ({ value, onChange }: Props) => {
  const modes = [
    {
      id: "1",
      name: "Crescimento Orgânico",
      desc: "Recomendado para perfis novos",
      icon: Target,
    },
    {
      id: "2",
      name: "Engajamento Agressivo",
      desc: "Perfis farmados em alto volume",
      icon: Zap,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4">
      {modes.map((mode) => (
        <motion.button
          key={mode.id}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onChange(mode.id)}
          className={`relative text-left p-4 rounded-2xl border transition-all duration-300 ${
            value === mode.id
              ? "bg-card border-border shadow-lg"
              : "bg-background/50 border-transparent hover:bg-card/50"
          }`}
        >
          <div className="flex items-start gap-4">
             <div className={`p-2 rounded-xl flex-none ${value === mode.id ? 'bg-primary/20' : 'bg-muted'}`}>
                <mode.icon className={`w-5 h-5 ${value === mode.id ? 'text-primary' : 'text-muted-foreground'}`} />
             </div>
             <div>
               <h3 className={`font-display font-bold text-sm tracking-tight mb-1 ${value === mode.id ? 'text-foreground' : 'text-muted-foreground'}`}>
                 {mode.name}
               </h3>
               <p className={`text-[10px] leading-tight ${value === mode.id ? 'text-foreground/70' : 'text-muted-foreground/50'}`}>
                 {mode.desc}
               </p>
             </div>
          </div>
          {value === mode.id && (
             <motion.div layoutId="strategy-active" className="absolute bottom-4 left-16 right-4 h-[3px] bg-primary rounded-full shadow-[0_0_10px_rgba(251,191,36,0.6)]" />
          )}
        </motion.button>
      ))}
    </div>
  );
};

export default StrategySelector;
