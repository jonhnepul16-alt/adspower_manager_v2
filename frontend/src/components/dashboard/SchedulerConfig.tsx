import { useState, useEffect } from "react";
import { Clock, Repeat, Timer, CalendarClock, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Props {
  config: any;
  status: any;
  onUpdate: (config: any) => void;
}

const SchedulerConfig = ({ config, status, onUpdate }: Props) => {
  const [startTime, setStartTime] = useState("00:00");
  const [endTime, setEndTime] = useState("06:00");
  const [warmupDuration, setWarmupDuration] = useState(15);
  const [repetitions, setRepetitions] = useState(1);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Sync from server config
  useEffect(() => {
    if (config) {
      if (config.start_time) setStartTime(config.start_time);
      if (config.end_time) setEndTime(config.end_time);
      if (config.warmup_duration) setWarmupDuration(config.warmup_duration);
      if (config.repetitions) setRepetitions(config.repetitions);
    }
  }, [config]);

  if (!config) return <div className="text-muted-foreground text-xs animate-pulse">Carregando...</div>;

  const isActive = !!config.active;

  const markDirty = () => setHasUnsavedChanges(true);

  const handleConfirm = () => {
    onUpdate({
      ...config,
      start_time: startTime,
      end_time: endTime,
      warmup_duration: warmupDuration,
      repetitions: repetitions,
    });
    setHasUnsavedChanges(false);
  };

  const pendingSessions = status?.pending_sessions ?? 0;
  const totalSessions = status?.total_sessions ?? 0;

  // When scheduler is OFF, show nothing (parent handles the toggle)
  if (!isActive) {
    return (
      <p className="text-[9px] text-white/20 italic">
        Ative o agendamento para configurar horários automáticos.
      </p>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className="flex flex-col gap-4"
    >
      {/* Time Window */}
      <div className="space-y-2">
        <label className="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] flex items-center gap-1.5">
          <Clock className="w-3 h-3" />
          Janela de Horário
        </label>
        <div className="flex items-center gap-2">
          <input
            type="time"
            value={startTime}
            onChange={(e) => { setStartTime(e.target.value); markDirty(); }}
            className="flex-1 bg-white/[0.03] border border-white/[0.06] rounded-lg px-3 py-2.5 text-xs text-foreground font-mono outline-none focus:border-primary/40 transition-all"
          />
          <span className="text-[9px] font-black text-white/15 uppercase">até</span>
          <input
            type="time"
            value={endTime}
            onChange={(e) => { setEndTime(e.target.value); markDirty(); }}
            className="flex-1 bg-white/[0.03] border border-white/[0.06] rounded-lg px-3 py-2.5 text-xs text-foreground font-mono outline-none focus:border-primary/40 transition-all"
          />
        </div>
      </div>

      {/* Warmup Duration */}
      <div className="space-y-2">
        <label className="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] flex items-center gap-1.5">
          <Timer className="w-3 h-3" />
          Duração do Aquecimento
        </label>
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-display font-black text-primary">{warmupDuration} min</span>
          </div>
          <input
            type="range"
            min={5}
            max={60}
            step={5}
            value={warmupDuration}
            onChange={(e) => { setWarmupDuration(parseInt(e.target.value)); markDirty(); }}
            className="w-full accent-primary h-1 bg-white/10 rounded-full appearance-none cursor-pointer"
          />
          <div className="flex justify-between mt-1">
            <span className="text-[8px] text-white/15 font-mono">5m</span>
            <span className="text-[8px] text-white/15 font-mono">60m</span>
          </div>
        </div>
      </div>

      {/* Repetitions */}
      <div className="space-y-2">
        <label className="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] flex items-center gap-1.5">
          <Repeat className="w-3 h-3" />
          Aberturas por Perfil
        </label>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              onClick={() => { setRepetitions(n); markDirty(); }}
              className={`flex-1 py-2.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all border
                ${repetitions === n
                  ? "bg-primary/15 border-primary/40 text-primary shadow-[0_0_12px_rgba(240,90,40,0.15)]"
                  : "bg-white/[0.02] border-white/[0.05] text-white/30 hover:border-white/10 hover:text-white/50"
                }
              `}
            >
              {n}x
            </button>
          ))}
        </div>
      </div>

      {/* Confirm Button */}
      <button
        onClick={handleConfirm}
        className={`w-full py-3.5 rounded-xl font-display font-black text-[10px] uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-2
          ${hasUnsavedChanges
            ? "bg-primary text-primary-foreground shadow-[0_0_20px_rgba(240,90,40,0.3)] hover:shadow-[0_0_30px_rgba(240,90,40,0.5)] hover:-translate-y-0.5"
            : "bg-white/[0.03] border border-white/[0.06] text-white/30 cursor-default"
          }
        `}
      >
        <Check className="w-3.5 h-3.5" />
        {hasUnsavedChanges ? "CONFIRMAR AGENDAMENTO" : "AGENDAMENTO SALVO"}
      </button>

      {/* Status Preview */}
      {totalSessions > 0 && !hasUnsavedChanges && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-emerald-500/[0.06] border border-emerald-500/20 rounded-xl p-3 space-y-1"
        >
          <div className="flex items-center gap-2">
            <CalendarClock className="w-3.5 h-3.5 text-emerald-500" />
            <span className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">
              {pendingSessions} sessões restantes hoje
            </span>
          </div>

          {/* Show next slots */}
          {config._slots && config._slots.length > 0 && (
            <div className="mt-2 space-y-1 max-h-24 overflow-y-auto hide-scrollbar">
              {config._slots
                .filter((s: any) => !s.executed)
                .slice(0, 5)
                .map((slot: any, i: number) => (
                  <div
                    key={i}
                    className="flex items-center justify-between px-2 py-1 bg-white/[0.02] rounded-md"
                  >
                    <span className="text-[9px] font-mono text-emerald-400/80">{slot.time}</span>
                    <span className="text-[8px] font-bold text-white/20 uppercase truncate max-w-[100px]">
                      {slot.profile_id}
                    </span>
                  </div>
                ))}
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};

export default SchedulerConfig;
