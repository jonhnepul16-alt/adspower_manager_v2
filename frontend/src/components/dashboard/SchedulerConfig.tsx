import { useState } from "react";
import { Clock, Key } from "lucide-react";
import { motion } from "framer-motion";

interface Props {
  config: any;
  status: any;
  onUpdate: (config: any) => void;
}

const SchedulerConfig = ({ config, status, onUpdate }: Props) => {
  const [enabled, setEnabled] = useState(config?.active || true);
  const [weekendMode, setWeekendMode] = useState(false);

  // Fallback se não for carregado
  if (!config) return <div className="text-muted-foreground text-xs animate-pulse">Carregando Módulos...</div>;

  const handleToggle = () => {
    const newState = !enabled;
    setEnabled(newState);
    onUpdate({ active: newState });
  };

  return (
    <div className="flex flex-col gap-4">
       {/* Card Principal - Horario Comercial */}
       <div className={`p-4 rounded-2xl border transition-all duration-300 flex items-center justify-between ${enabled ? 'bg-card border-border shadow-lg' : 'bg-background/50 border-transparent hover:bg-card/50'}`}>
          <div className="flex items-center gap-4">
             <div className={`w-8 h-8 rounded-full flex items-center justify-center ${enabled ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'}`}>
                <Clock className="w-4 h-4" />
             </div>
             <div>
                <h4 className={`text-[11px] font-bold ${enabled ? 'text-foreground' : 'text-foreground/70'}`}>Horário Comercial</h4>
                <p className="text-[10px] text-muted-foreground/60 leading-tight">09:00 - 18:00<br/>(BRT)</p>
             </div>
          </div>
          <button 
             onClick={handleToggle}
             className={`w-12 h-6 rounded-full transition-colors relative flex items-center px-1 ${enabled ? 'bg-emerald-500' : 'bg-muted-foreground/30'}`}
          >
             <motion.div 
               animate={{ x: enabled ? 24 : 0 }}
               className="w-4 h-4 bg-white rounded-full shadow-sm"
             />
          </button>
       </div>

       {/* Final de semana - Opcional Fake Visual */}
       <div className={`p-4 rounded-2xl border transition-all duration-300 flex items-center justify-between ${weekendMode ? 'bg-card border-border shadow-lg' : 'bg-background/50 border-transparent hover:bg-card/50'}`}>
          <div className="flex items-center gap-4">
             <div className={`w-8 h-8 rounded-full flex items-center justify-center ${weekendMode ? 'bg-primary/20 text-primary' : 'bg-muted/50 text-muted-foreground'}`}>
                <Key className="w-4 h-4" />
             </div>
             <div>
                <h4 className={`text-[11px] font-bold ${weekendMode ? 'text-foreground' : 'text-foreground/70'}`}>Final de Semana</h4>
                <p className="text-[10px] text-muted-foreground/60 leading-tight">Frequência<br/>reduzida</p>
             </div>
          </div>
          <button 
             onClick={() => setWeekendMode(!weekendMode)}
             className={`w-12 h-6 rounded-full transition-colors relative flex items-center px-1 ${weekendMode ? 'bg-emerald-500' : 'bg-muted-foreground/30'}`}
          >
             <motion.div 
               animate={{ x: weekendMode ? 24 : 0 }}
               className="w-4 h-4 bg-white rounded-full shadow-sm"
             />
          </button>
       </div>
    </div>
  );
};

export default SchedulerConfig;
