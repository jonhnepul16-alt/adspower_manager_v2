import { useState, useEffect } from "react";
import { CalendarClock, Clock, Timer, Repeat, Check, Users, Search, X, Play, Pause, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import HeaderBar from "@/components/dashboard/HeaderBar";
import GlassCard from "@/components/dashboard/GlassCard";
import { toast } from "sonner";
import { fetchProfiles, fetchStatus, updateScheduler } from "@/lib/api";
import { supabase } from "@/lib/supabase";

interface Profile {
  id: string;
  name: string;
  adsPowerId: string;
  tag: string;
}

const Scheduler = () => {
  const navigate = useNavigate();
  const [machineId] = useState(() => localStorage.getItem("vexel_machine_id") || "local_agent");
  const [userEmail, setUserEmail] = useState<string>("");

  useEffect(() => {
    const getUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user?.email) {
        setUserEmail(session.user.email);
      }
    };
    getUser();
  }, []);

  // Scheduler config state
  const [isActive, setIsActive] = useState(false);
  const [startTime, setStartTime] = useState("00:00");
  const [endTime, setEndTime] = useState("06:00");
  const [warmupDuration, setWarmupDuration] = useState(15);
  const [repetitions, setRepetitions] = useState(1);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Profile selection
  const [allProfiles, setAllProfiles] = useState<Profile[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  // Status from server
  const [slots, setSlots] = useState<any[]>([]);
  const [pendingSessions, setPendingSessions] = useState(0);
  const [totalSessions, setTotalSessions] = useState(0);
  const [serverConfig, setServerConfig] = useState<any>(null);
  const [planTier, setPlanTier] = useState<string>("START");

  // Load profiles
  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchProfiles();
        setAllProfiles(
          (data || []).map((p: any) => ({
            id: p.id,
            name: p.name,
            tag: p.tag,
            adsPowerId: p.id,
          }))
        );
      } catch (e) {
        console.error("Failed to load profiles", e);
      }
    };
    load();
  }, []);

  // Poll server status (only sync config when user is NOT editing)
  const [initialLoaded, setInitialLoaded] = useState(false);

  useEffect(() => {
    const poll = async () => {
      try {
        const status = await fetchStatus(machineId);
        const cfg = status.scheduler_config || {};
        const sts = status.scheduler_status || {};
        const tier = status.plan_status?.plan || "START";

        setPlanTier(tier);
        setServerConfig(cfg);
        setIsActive(!!cfg.active);
        setPendingSessions(sts.pending_sessions ?? 0);
        setTotalSessions(sts.total_sessions ?? 0);
        setSlots(cfg._slots || []);

        // Only sync form fields from server if user is NOT actively editing
        if (!hasUnsavedChanges && !initialLoaded) {
          if (cfg.start_time) setStartTime(cfg.start_time);
          if (cfg.end_time) setEndTime(cfg.end_time);
          if (cfg.warmup_duration) setWarmupDuration(cfg.warmup_duration);
          if (cfg.repetitions) setRepetitions(cfg.repetitions);
          if (cfg.profile_ids) setSelectedIds(cfg.profile_ids);
          setInitialLoaded(true);
        }
      } catch (e) {
        console.error(e);
      }
    };
    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, [machineId, hasUnsavedChanges, initialLoaded]);

  const toggleProfile = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    setHasUnsavedChanges(true);
  };

  const selectAll = () => {
    if (selectedIds.length === allProfiles.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(allProfiles.map((p) => p.id));
    }
    setHasUnsavedChanges(true);
  };

  const handleSave = async () => {
    if (selectedIds.length === 0) {
      toast.error("Selecione pelo menos um perfil para agendar!");
      return;
    }
    try {
      await updateScheduler(machineId, {
        ...(serverConfig || {}),
        active: isActive,
        start_time: startTime,
        end_time: endTime,
        warmup_duration: warmupDuration,
        repetitions: repetitions,
        profile_ids: selectedIds,
      });
      setHasUnsavedChanges(false);
      toast.success("Agendamento salvo com sucesso!");
    } catch (err) {
      toast.error("Erro ao salvar agendamento");
    }
  };

  const handleToggle = async () => {
    const newActive = !isActive;
    setIsActive(newActive);
    try {
      await updateScheduler(machineId, {
        ...(serverConfig || {}),
        active: newActive,
        start_time: startTime,
        end_time: endTime,
        warmup_duration: warmupDuration,
        repetitions: repetitions,
        profile_ids: selectedIds,
      });
      toast.success(newActive ? "Agendamento ATIVADO!" : "Agendamento PAUSADO!");
    } catch (err) {
      setIsActive(!newActive);
      toast.error("Erro ao alterar agendamento");
    }
  };

  const filteredProfiles = allProfiles.filter(
    (p) =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.tag?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const pendingSlots = slots.filter((s) => !s.executed);

  return (
    <div className="min-h-screen bg-background text-foreground font-body">
      <HeaderBar
        isActive={false}
        apiKey={machineId}
        onApiKeyChange={() => {}}
        userEmail={userEmail}
        plan={planTier}
      />

      <main className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <CalendarClock className="w-5 h-5 text-primary" />
              <h1 className="font-display text-2xl font-black text-foreground tracking-tight uppercase">
                Agendamento
              </h1>
            </div>
            <p className="text-sm text-muted-foreground">
              Configure horários automáticos de aquecimento para seus perfis.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleToggle}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-full font-display font-bold text-[10px] uppercase tracking-widest transition-all ${
                isActive
                  ? "bg-emerald-500/20 border border-emerald-500/40 text-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.2)]"
                  : "bg-white/5 border border-white/10 text-muted-foreground hover:border-white/20"
              }`}
            >
              {isActive ? (
                <>
                  <Pause className="w-3.5 h-3.5" /> PAUSAR
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" /> ATIVAR
                </>
              )}
            </button>
          </div>
        </div>

        <div className="relative">
          <div className={`grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-8 transition-all ${planTier === "START" ? "blur-md pointer-events-none select-none opacity-40" : ""}`}>
            {/* LEFT: Configuration */}
            <div className="flex flex-col gap-6">
              <GlassCard className="p-6">
                <h2 className="text-[10px] font-black text-foreground uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 text-primary" />
                  Configurações do Agendamento
                </h2>

                <div className="space-y-6">
                  {/* Time Window */}
                  <div className="space-y-2">
                    <label className="text-[9px] font-black text-white/30 uppercase tracking-[0.15em]">
                      Janela de Horário
                    </label>
                    <div className="flex items-center gap-3">
                      <input
                        type="time"
                        value={startTime}
                        onChange={(e) => {
                          setStartTime(e.target.value);
                          setHasUnsavedChanges(true);
                        }}
                        className="flex-1 bg-white/[0.03] border border-white/[0.06] rounded-xl px-4 py-3 text-sm text-foreground font-mono outline-none focus:border-primary/40 transition-all"
                      />
                      <ChevronRight className="w-4 h-4 text-white/15" />
                      <input
                        type="time"
                        value={endTime}
                        onChange={(e) => {
                          setEndTime(e.target.value);
                          setHasUnsavedChanges(true);
                        }}
                        className="flex-1 bg-white/[0.03] border border-white/[0.06] rounded-xl px-4 py-3 text-sm text-foreground font-mono outline-none focus:border-primary/40 transition-all"
                      />
                    </div>
                    <p className="text-[8px] text-white/15 italic">
                      Suporta horários noturnos (ex: 22:00 → 06:00)
                    </p>
                  </div>

                  {/* Duration */}
                  <div className="space-y-2">
                    <label className="text-[9px] font-black text-white/30 uppercase tracking-[0.15em] flex items-center gap-1.5">
                      <Timer className="w-3 h-3" /> Duração por perfil
                    </label>
                    <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-lg font-display font-black text-primary">
                          {warmupDuration} min
                        </span>
                        <span className="text-[8px] font-mono text-white/15">
                          5m — 60m
                        </span>
                      </div>
                      <input
                        type="range"
                        min={5}
                        max={60}
                        step={5}
                        value={warmupDuration}
                        onChange={(e) => {
                          setWarmupDuration(parseInt(e.target.value));
                          setHasUnsavedChanges(true);
                        }}
                        className="w-full accent-primary h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer"
                      />
                    </div>
                  </div>

                  {/* Repetitions */}
                  <div className="space-y-2">
                    <label className="text-[9px] font-black text-white/30 uppercase tracking-[0.15em] flex items-center gap-1.5">
                      <Repeat className="w-3 h-3" /> Aberturas por perfil
                    </label>
                    <div className="grid grid-cols-5 gap-2">
                      {[1, 2, 3, 4, 5].map((n) => (
                        <button
                          key={n}
                          onClick={() => {
                            setRepetitions(n);
                            setHasUnsavedChanges(true);
                          }}
                          className={`py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all border
                            ${
                              repetitions === n
                                ? "bg-primary/15 border-primary/40 text-primary shadow-[0_0_15px_rgba(240,90,40,0.15)]"
                                : "bg-white/[0.02] border-white/[0.05] text-white/30 hover:border-white/10"
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
                    onClick={handleSave}
                    disabled={!hasUnsavedChanges}
                    className={`w-full py-4 rounded-xl font-display font-black text-xs uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-2
                      ${
                        hasUnsavedChanges
                          ? "bg-primary text-primary-foreground shadow-[0_0_25px_rgba(240,90,40,0.3)] hover:shadow-[0_0_35px_rgba(240,90,40,0.5)] hover:-translate-y-0.5"
                          : "bg-white/[0.03] border border-white/[0.06] text-white/20 cursor-not-allowed"
                      }
                    `}
                  >
                    <Check className="w-4 h-4" />
                    {hasUnsavedChanges
                      ? "CONFIRMAR AGENDAMENTO"
                      : "AGENDAMENTO SALVO"}
                  </button>
                </div>
              </GlassCard>

              {/* Slots Preview */}
              {isActive && pendingSlots.length > 0 && (
                <GlassCard className="p-6">
                  <h2 className="text-[10px] font-black text-emerald-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                    <CalendarClock className="w-3.5 h-3.5" />
                    Próximas Sessões ({pendingSessions} restantes)
                  </h2>
                  <div className="space-y-2 max-h-[300px] overflow-y-auto hide-scrollbar">
                    {pendingSlots.map((slot, i) => {
                      const profile = allProfiles.find(
                        (p) => p.id === slot.profile_id
                      );
                      return (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.03 }}
                          className="flex items-center justify-between p-3 bg-white/[0.02] border border-white/[0.05] rounded-xl"
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-mono font-black text-emerald-400">
                              {slot.time}
                            </span>
                            <div className="w-px h-4 bg-white/10" />
                            <span className="text-[10px] font-bold text-foreground truncate max-w-[150px]">
                              {profile?.name || slot.profile_id}
                            </span>
                          </div>
                          <span className="text-[8px] font-bold text-white/20 uppercase tracking-widest">
                            {warmupDuration}min
                          </span>
                        </motion.div>
                      );
                    })}
                  </div>
                </GlassCard>
              )}
            </div>

            {/* RIGHT: Profile Selection */}
            <GlassCard className="p-6 h-fit">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-[10px] font-black text-foreground uppercase tracking-[0.2em] flex items-center gap-2">
                  <Users className="w-3.5 h-3.5 text-primary" />
                  Perfis para Agendar
                </h2>
                <span className="text-[9px] font-bold text-primary">
                  {selectedIds.length}/{allProfiles.length}
                </span>
              </div>

              <div className="flex items-center gap-3 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground/30" />
                  <input
                    type="text"
                    placeholder="Buscar perfil..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full bg-white/[0.03] border border-white/[0.05] rounded-full pl-9 pr-4 py-2 text-[10px] focus:outline-none focus:border-primary/30 transition-all"
                  />
                </div>
                <button
                  onClick={selectAll}
                  className="text-[8px] font-black text-primary uppercase tracking-widest whitespace-nowrap hover:underline"
                >
                  {selectedIds.length === allProfiles.length
                    ? "LIMPAR"
                    : "TODOS"}
                </button>
              </div>

              <div className="space-y-2 max-h-[500px] overflow-y-auto hide-scrollbar">
                {allProfiles.length === 0 ? (
                  <div className="py-12 flex flex-col items-center justify-center text-center opacity-30">
                    <Users className="w-10 h-10 mb-3" />
                    <p className="text-xs font-bold uppercase tracking-widest">
                      Nenhum perfil cadastrado
                    </p>
                    <button
                      onClick={() => navigate("/profiles")}
                      className="mt-2 text-primary text-[10px] font-black underline"
                    >
                      CADASTRAR PERFIS
                    </button>
                  </div>
                ) : (
                  filteredProfiles.map((p) => {
                    const isSelected = selectedIds.includes(p.id);
                    return (
                      <button
                        key={p.id}
                        onClick={() => toggleProfile(p.id)}
                        className={`w-full flex items-center gap-3 p-3.5 rounded-xl border transition-all text-left
                          ${
                            isSelected
                              ? "bg-primary/[0.06] border-primary/30 shadow-[0_0_12px_rgba(240,90,40,0.08)]"
                              : "bg-white/[0.02] border-white/[0.05] hover:border-white/10"
                          }
                        `}
                      >
                        <div
                          className={`w-5 h-5 rounded-full border flex items-center justify-center transition-all shrink-0
                          ${
                            isSelected
                              ? "bg-primary border-primary"
                              : "border-white/10 bg-white/5"
                          }
                        `}
                        >
                          {isSelected && (
                            <Check className="w-3 h-3 text-primary-foreground stroke-[3]" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <span
                            className={`text-xs font-bold truncate block ${
                              isSelected ? "text-primary" : "text-foreground"
                            }`}
                          >
                            {p.name}
                          </span>
                          <div className="flex items-center gap-2 mt-0.5">
                            <code className="text-[8px] text-muted-foreground font-mono bg-white/[0.03] px-1.5 py-0.5 rounded">
                              {p.id}
                            </code>
                            <span className="text-[8px] font-black text-white/15 uppercase">
                              {p.tag}
                            </span>
                          </div>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </GlassCard>
          </div>

          {/* Locked Overlay */}
          {planTier === "START" && (
            <div className="absolute inset-0 z-10 flex items-center justify-center p-6 bg-slate-950/20 rounded-3xl">
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-md w-full bg-slate-900/90 border border-white/10 backdrop-blur-xl rounded-3xl p-8 text-center shadow-[0_0_50px_rgba(0,0,0,0.5)]"
              >
                <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <CalendarClock className="w-8 h-8 text-primary" />
                </div>
                <h3 className="font-display text-2xl font-black text-foreground mb-3 uppercase tracking-tight">
                  Recurso Exclusivo
                </h3>
                <p className="text-sm text-muted-foreground mb-8 leading-relaxed">
                  O agendamento automático de aquecimento está disponível apenas para usuários do plano <span className="text-primary font-bold">Scale</span>.
                </p>
                <div className="space-y-4">
                  <button 
                    onClick={() => window.open("https://warmads.com/#pricing", "_blank")}
                    className="w-full py-4 rounded-xl bg-primary text-primary-foreground font-display font-black text-xs uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(240,90,40,0.3)] hover:shadow-[0_0_30px_rgba(240,90,40,0.5)] transition-all"
                  >
                    FAZER UPGRADE AGORA
                  </button>
                  <button 
                    onClick={() => navigate("/")}
                    className="w-full py-4 rounded-xl bg-white/5 border border-white/10 text-white/40 font-display font-black text-xs uppercase tracking-[0.2em] hover:bg-white/10 transition-all"
                  >
                    VOLTAR AO DASHBOARD
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Scheduler;
