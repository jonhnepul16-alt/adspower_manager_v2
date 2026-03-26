import { useEffect, useState } from "react";
import { Clock, Zap, Settings, Shield } from "lucide-react";
import GlassCard from "./GlassCard";
import { motion } from "framer-motion";

interface SchedulerConfigProps {
  config: any;
  status: any;
  onUpdate: (newConfig: any) => void;
}

const SchedulerConfig = ({ config, status, onUpdate }: SchedulerConfigProps) => {
  const [localConfig, setLocalConfig] = useState(config || {
    active: false,
    windows: {
      morning: { enabled: true, start: "08:00", end: "12:00", frequency: "medium" },
      afternoon: { enabled: true, start: "13:00", end: "18:00", frequency: "medium" },
      night: { enabled: true, start: "19:00", end: "23:00", frequency: "medium" }
    },
    intensity: "normal",
    style: "normal",
    daily_limit: 15
  });

  const handleChange = (key: string, value: any) => {
    const updated = { ...localConfig, [key]: value };
    setLocalConfig(updated);
  };

  // Sync local state when config from API changes
  useEffect(() => {
    if (config) {
      setLocalConfig(config);
    }
  }, [config]);

  const handleWindowChange = (window: string, field: string, value: any) => {
    const updated = {
      ...localConfig,
      windows: {
        ...localConfig.windows,
        [window]: { ...localConfig.windows[window], [field]: value }
      }
    };
    setLocalConfig(updated);
  };

  const handleSave = () => {
    onUpdate(localConfig);
  };

  return (
    <GlassCard className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-xl ${localConfig.active ? 'bg-primary/20 animate-pulse' : 'bg-muted'}`}>
            <Clock className={`w-5 h-5 ${localConfig.active ? 'text-primary' : 'text-muted-foreground'}`} />
          </div>
          <div>
            <h2 className="font-display font-bold text-xs text-foreground uppercase tracking-widest leading-none">
              Agendamento Inteligente
            </h2>
            <p className="text-[10px] text-muted-foreground mt-1 font-medium">
              {localConfig.active ? "SISTEMA OPERACIONAL" : "SISTEMA EM ESPERA"}
            </p>
          </div>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => {
            const nextActive = !localConfig.active;
            const updated = { ...localConfig, active: nextActive };
            setLocalConfig(updated);
            onUpdate(updated);
          }}
          className={`relative flex items-center gap-2 px-6 py-2.5 rounded-2xl text-[10px] font-bold uppercase tracking-[0.15em] transition-all overflow-hidden ${
            localConfig.active 
              ? "bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-400 border border-emerald-500/30 glow-emerald" 
              : "bg-muted text-muted-foreground border border-border"
          }`}
        >
          {localConfig.active && (
            <span className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-transparent animate-shimmer" />
          )}
          <div className={`w-2 h-2 rounded-full ${localConfig.active ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]' : 'bg-muted-foreground/40'}`} />
          {localConfig.active ? "ATIVADO" : "DESATIVADO"}
        </motion.button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(localConfig.windows).map(([name, win]: [string, any]) => (
          <div key={name} className="p-4 rounded-2xl bg-muted/20 border border-border/50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase opacity-60">{name === 'morning' ? 'Manhã' : name === 'afternoon' ? 'Tarde' : 'Noite'}</span>
              <input 
                type="checkbox" 
                checked={win.enabled} 
                onChange={(e) => handleWindowChange(name, "enabled", e.target.checked)}
                className="w-3 h-3 accent-primary"
              />
            </div>
            <div className="flex gap-2 text-[10px] items-center">
              <input 
                type="text" 
                value={win.start} 
                onChange={(e) => handleWindowChange(name, "start", e.target.value)}
                className="bg-transparent border-b border-border w-10 text-center"
              />
              <span>-</span>
              <input 
                type="text" 
                value={win.end} 
                onChange={(e) => handleWindowChange(name, "end", e.target.value)}
                className="bg-transparent border-b border-border w-10 text-center"
              />
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-[10px] font-bold uppercase opacity-40 flex items-center gap-1">
            <Zap className="w-3 h-3" /> Intensidade
          </label>
          <select 
            value={localConfig.intensity}
            onChange={(e) => handleChange("intensity", e.target.value)}
            className="w-full bg-muted/30 border border-border rounded-lg px-3 py-2 text-[11px] focus:outline-none focus:border-primary/40"
          >
            <option value="low" className="bg-slate-900">Baixa (Poupando)</option>
            <option value="normal" className="bg-slate-900">Normal (Humano)</option>
            <option value="high" className="bg-slate-900">Alta (Explorador)</option>
          </select>
        </div>

        <div className="space-y-2">
          <label className="text-[10px] font-bold uppercase opacity-40 flex items-center gap-1">
            <Shield className="w-3 h-3" /> Limite Diário
          </label>
          <input 
            type="number"
            value={localConfig.daily_limit}
            onChange={(e) => handleChange("daily_limit", parseInt(e.target.value))}
            className="w-full bg-muted/30 border border-border rounded-lg px-3 py-2 text-[11px] focus:outline-none focus:border-primary/40"
          />
        </div>
      </div>

      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={handleSave}
        className="w-full py-4 bg-primary text-primary-foreground rounded-2xl text-[10px] font-bold uppercase tracking-[0.2em] transition-all shadow-lg shadow-primary/20 hover:shadow-primary/40 relative overflow-hidden group"
      >
        <span className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
        Sincronizar e Salvar Alterações
      </motion.button>

      {status?.next_sessions && Object.keys(status.next_sessions).length > 0 && (
        <div className="mt-2 p-5 rounded-3xl bg-primary/5 border border-primary/10 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
             <h3 className="text-[10px] font-bold uppercase text-primary tracking-widest opacity-80">Próximas Sessões Estimadas</h3>
             <div className="flex gap-1">
                <span className="w-1 h-1 rounded-full bg-primary/40" />
                <span className="w-1 h-1 rounded-full bg-primary/20" />
             </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Object.entries(status.next_sessions).map(([pid, time]: [string, any]) => (
              <div key={pid} className="flex flex-col gap-1 p-3 bg-background/40 rounded-xl border border-border/50 hover:border-primary/30 transition-colors group">
                <span className="text-[10px] font-mono text-muted-foreground group-hover:text-primary transition-colors">ID: {pid.slice(-6)}</span>
                <span className="text-xs font-bold text-foreground">{time}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </GlassCard>
  );
};

export default SchedulerConfig;
