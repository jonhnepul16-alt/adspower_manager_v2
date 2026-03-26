import { useState } from "react";
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
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-primary" />
          <h2 className="font-display font-semibold text-sm text-foreground uppercase tracking-widest text-[10px] opacity-60">
            Agendamento Inteligente
          </h2>
        </div>
        <button
          onClick={() => handleChange("active", !localConfig.active)}
          className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${
            localConfig.active 
              ? "bg-primary/20 text-primary border border-primary/30" 
              : "bg-muted text-muted-foreground border border-border"
          }`}
        >
          {localConfig.active ? "ATIVO" : "INATIVO"}
        </button>
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
        className="w-full py-3 bg-primary/10 hover:bg-primary/20 border border-primary/20 text-primary rounded-2xl text-[10px] font-bold uppercase tracking-widest transition-all"
      >
        Salvar Configuração de Agendamento
      </motion.button>

      {status?.next_sessions && Object.keys(status.next_sessions).length > 0 && (
        <div className="mt-2 p-4 rounded-2xl bg-primary/5 border border-primary/10">
          <h3 className="text-[9px] font-bold uppercase opacity-50 mb-3 tracking-wider">Próximas Sessões Estimadas</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(status.next_sessions).map(([pid, time]: [string, any]) => (
              <div key={pid} className="flex items-center gap-2 px-3 py-1.5 bg-background/50 rounded-lg border border-border/50">
                <span className="text-[10px] font-mono opacity-60">{pid.slice(-6)}</span>
                <span className="text-[10px] font-bold text-primary">{time}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </GlassCard>
  );
};

export default SchedulerConfig;
