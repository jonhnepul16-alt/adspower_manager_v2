import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Users, Heart, Play, MessageSquare, Zap, Search, Tag as TagIcon, X as CloseIcon, Check, ChevronRight, LayoutGrid, ListFilter, Clock, Minus, Plus, Copy } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import HeaderBar from "@/components/dashboard/HeaderBar";
import GlassCard from "@/components/dashboard/GlassCard";
import StrategySelector from "@/components/dashboard/StrategySelector";
import LogTerminal from "@/components/dashboard/LogTerminal";
import ActionBarChart from "@/components/dashboard/ActionBarChart";
import ExecutionList from "@/components/dashboard/ExecutionList";
import StatCard from "@/components/dashboard/StatCard";
import OnboardingBanner from "@/components/dashboard/OnboardingBanner";
import { fetchStatus, startWarmup, stopWarmup, fetchProfiles } from "@/lib/api";
import { Cloud, Calendar, TrendingUp, Activity } from "lucide-react";
import { toast } from "sonner";


interface Profile {
  id: string;
  name: string;
  adsPowerId: string;
  tag: string;
}

type ProfileResult = {
  ok: boolean;
  curtidas_feed?: number;
  reacoes_dadas?: number;
  comentarios_feitos?: number;
  reels_assistidos?: number;
  postagem?: boolean;
  grupos_visitados?: number;
  amigos_adicionados?: number;
};

const Index = () => {
  const [isActive, setIsActive] = useState(false);
  const [isAgentConnected, setIsAgentConnected] = useState(true);
  const [cloudConnected, setCloudConnected] = useState(false);
  const [selectedProfiles, setSelectedProfiles] = useState<Profile[]>([]);
  const [selectedMode, setSelectedMode] = useState("1");
  const [logs, setLogs] = useState<string[]>([]);
  const [results, setResults] = useState<Record<string, ProfileResult>>({});
  const [schedulerConfig, setSchedulerConfig] = useState<any>(null);
  const [schedulerStatus, setSchedulerStatus] = useState<any>(null);
  const [schedulerActive, setSchedulerActive] = useState(false);
  const [currentProfile, setCurrentProfile] = useState<string | null>(null);
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const [planLimits, setPlanLimits] = useState<any>(null);
  const [warmupDuration, setWarmupDuration] = useState<number | null>(null);
  const [adsApiKey, setAdsApiKey] = useState(() => localStorage.getItem("adspower_api_key") || "");
  const [machineId, setMachineId] = useState(() => {
    // 1. Tenta pegar do localStorage ou "default"
    return localStorage.getItem("vexel_machine_id") || "local_agent";
  });

  const safeResults = results ?? {};

  // Detect if running in Electron (local) or browser (cloud site)
  const isElectron = typeof window !== 'undefined' && window.process && (window.process as any).type === 'renderer';
  
  // Connection state for onboarding banner (cloud site only)
  const [bannerDismissed, setBannerDismissed] = useState(false);
  
  const connectionState = (() => {
    if (isElectron) return "connected" as const;  // Local app, always connected
    if (cloudConnected) return "connected" as const;
    // Check if user ever had SAS by looking at localStorage
    const savedId = localStorage.getItem("vexel_machine_id");
    if (savedId && savedId !== "local_agent") return "sas_offline" as const;
    return "no_sas" as const;
  })();

  // Persist API Key changes
  useEffect(() => {
    localStorage.setItem("vexel_machine_id", machineId);
  }, [machineId]);

  useEffect(() => {
    const saved = localStorage.getItem("selected_profiles");
    if (saved) {
      try {
        setSelectedProfiles(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to load selected profiles", e);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("selected_profiles", JSON.stringify(selectedProfiles));
  }, [selectedProfiles]);

  const profileIds = selectedProfiles.map(p => p.adsPowerId);

  useEffect(() => {
    const check = async () => {
      try {
        const status = await fetchStatus(machineId);
        if (!status) return;
        
        setIsActive(status.is_running ?? false);
        // Logs: pull real messages from backend
        if (Array.isArray(status.logs)) setLogs(status.logs);
        setResults(status.results ?? {});
        const cfg = status.scheduler_config ?? null;
        setSchedulerConfig(cfg);
        setSchedulerStatus(status.scheduler_status ?? null);
        setCurrentProfile(status.current_profile ?? null);
        
        if (status.plan_status?.limits) {
          setPlanLimits(status.plan_status.limits);
        }
        setCloudConnected(status.cloud_connected ?? false);
        if (status.machine_id) setMachineId(status.machine_id);
        // Sync scheduler active state from server
        if (cfg && cfg.active !== undefined) {
          setSchedulerActive(!!cfg.active);
        }
      } catch (err) {
        console.error("Failed to fetch status", err);
      }
    };

    check();
    const interval = setInterval(check, 1000);
    return () => clearInterval(interval);
  }, [machineId]);

  const handleStart = async () => {
    console.log("Iniciando warmup para os IDs:", profileIds, "Duração:", warmupDuration);
    if (!profileIds.length) return;
    try {
      await startWarmup(profileIds, selectedMode, warmupDuration, machineId);
      setIsActive(true);
      toast.success("Comando de inicialização enviado!");
    } catch (err) {
      console.error(err);
      toast.error("Erro ao iniciar: " + (err instanceof Error ? err.message : "Erro desconhecido"));
    }
  };

  const handleStop = async () => {
    try {
      await stopWarmup(machineId);
      setIsActive(false);
      toast.success("Comando de parada enviado!");
    } catch (err) {
      console.error(err);
      toast.error("Erro ao parar: " + (err instanceof Error ? err.message : "Erro desconhecido"));
    }
  };



  const totalLikes = Object.values(safeResults).reduce((acc, r) => acc + (r.curtidas_feed || 0) + (r.reacoes_dadas || 0), 0);
  const totalComments = Object.values(safeResults).reduce((acc, r) => acc + (r.comentarios_feitos || 0), 0);
  const totalReels = Object.values(safeResults).reduce((acc, r) => acc + (r.reels_assistidos || 0), 0);
  const totalPosts = Object.values(safeResults).reduce((acc, r) => acc + (r.postagem ? 1 : 0), 0);
  const totalProfilesCount = selectedProfiles.length;

  const [savedProfiles, setSavedProfiles] = useState<any[]>([]);

  useEffect(() => {
    const loadProfiles = async () => {
      if (isPickerOpen) {
        try {
          const data = await fetchProfiles();
          // Transform if needed: backend uses 'id', component might expect 'id' but we should ensure mapping
          // The Profile interface uses 'adsPowerId' for some things and 'id' for others.
          // Let's ensure the data matches or is mapped correctly.
          setSavedProfiles(data.map((p: any) => ({
            id: p.id,
            name: p.name,
            tag: p.tag,
            adsPowerId: p.id // The backend 'id' is the AdsPower ID
          })));
        } catch (e) {
          console.error("Failed to fetch profiles from backend", e);
          toast.error("Erro ao carregar perfis do servidor");
        }
      }
    };
    loadProfiles();
  }, [isPickerOpen]);

  const toggleProfile = (profile: Profile) => {
    setSelectedProfiles(prev => {
      const exists = prev.find(p => p.id === profile.id);
      if (exists) {
        return prev.filter(p => p.id !== profile.id);
      } else {
        return [...prev, profile];
      }
    });
  };

  const selectAllProfiles = () => {
    if (selectedProfiles.length === savedProfiles.length) {
      setSelectedProfiles([]);
    } else {
      setSelectedProfiles(savedProfiles);
    }
  };

  const [pickerSearch, setPickerSearch] = useState("");
  const filteredSaved = savedProfiles.filter(p => 
    p.name.toLowerCase().includes(pickerSearch.toLowerCase()) ||
    p.tag.toLowerCase().includes(pickerSearch.toLowerCase()) ||
    p.adsPowerId.toLowerCase().includes(pickerSearch.toLowerCase())
  );


  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0A0A0A] flex flex-col">
      <HeaderBar
        isActive={isActive}
        isAgentConnected={isAgentConnected}
        apiKey={machineId}
        onApiKeyChange={setMachineId}
      />

      <main className="flex-1 p-4 lg:p-6 w-full max-w-full">
        {/* Onboarding Banner (cloud site only) */}
        {!isElectron && !bannerDismissed && connectionState !== "connected" && (
          <div className="mb-6">
            <OnboardingBanner
              connectionState={connectionState}
              onDismiss={() => setBannerDismissed(true)}
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[25fr_45fr_30fr] gap-4 items-start h-full">
          
          {/* COLUMN 1: CONTROLS (25%) */}
          <div className="flex flex-col gap-4">
             <GlassCard delay={0.1} className="p-4 border-l-2 border-l-primary/30">
                <div className="flex items-center justify-between mb-3">
                   <h2 className="text-[10px] font-black text-foreground uppercase tracking-[0.2em] flex items-center gap-2">
                     <Calendar className="w-3 h-3 text-primary" />
                     Agendamento
                   </h2>
                   <div className={`px-2 py-0.5 rounded-full border text-[8px] font-black ${schedulerActive ? "border-emerald-500/50 text-emerald-500" : "border-white/10 text-muted-foreground"}`}>
                      {schedulerActive ? "ON" : "OFF"}
                   </div>
                </div>
                <p className="text-[9px] text-white/30 mb-3">
                  {schedulerActive 
                    ? `${schedulerStatus?.pending_sessions ?? 0} sessões restantes hoje`
                    : "Configure horários automáticos de aquecimento"
                  }
                </p>
                <button 
                  onClick={() => navigate("/scheduler")}
                  className="w-full py-2.5 rounded-lg bg-white/[0.03] border border-white/[0.06] text-[9px] font-black text-primary uppercase tracking-widest hover:bg-primary/5 hover:border-primary/20 transition-all"
                >
                  CONFIGURAR →
                </button>
             </GlassCard>

             <GlassCard delay={0.2} className="p-4">
                <h2 className="text-[10px] font-black text-foreground uppercase tracking-[0.2em] mb-4">Configurações</h2>
                <div className="space-y-4">
                    <StrategySelector value={selectedMode} onChange={setSelectedMode} />
                    
                    <div className="space-y-2">
                       <label className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em] flex items-center gap-2">
                          <Clock className="w-3 h-3" />
                          Minutos por Perfil
                       </label>
                       
                       {planLimits ? (
                         <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-lg font-display font-black text-primary">
                                {warmupDuration === null ? "Auto" : `${warmupDuration}m`}
                              </span>
                              <span className="text-[8px] font-bold text-white/20 uppercase tracking-widest px-2 py-0.5 border border-white/5 rounded-full">
                                {planLimits.plan}
                              </span>
                            </div>
                            
                            <input 
                              type="range"
                              min={planLimits.session_time[0]}
                              max={planLimits.session_time[1]}
                              step={1}
                              value={warmupDuration === null ? planLimits.session_time[0] : warmupDuration}
                              onChange={(e) => setWarmupDuration(parseInt(e.target.value))}
                              className="w-full accent-primary h-1 bg-white/10 rounded-full appearance-none cursor-pointer"
                            />
                            
                            <div className="flex justify-between mt-2">
                               <button 
                                 onClick={() => setWarmupDuration(null)}
                                 className={`text-[8px] font-black uppercase tracking-widest ${warmupDuration === null ? 'text-primary' : 'text-white/20'}`}
                               >
                                 Randômico
                               </button>
                               <span className="text-[8px] font-mono text-white/10">{planLimits.session_time[0]}m-{planLimits.session_time[1]}m</span>
                            </div>
                         </div>
                       ) : (
                         <div className="animate-pulse bg-white/5 h-16 rounded-xl w-full" />
                       )}
                    </div>

                    {/* AdsPower API Key */}
                    <div className="space-y-2 pt-2 border-t border-white/[0.04]">
                       <label className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em] flex items-center gap-2">
                          🔑 API Key do AdsPower
                       </label>
                       <p className="text-[8px] text-white/15 -mt-1">Encontre em AdsPower → Settings → API</p>
                       <input
                         type="text"
                         value={adsApiKey}
                         onChange={(e) => {
                           setAdsApiKey(e.target.value);
                           localStorage.setItem("adspower_api_key", e.target.value);
                         }}
                         placeholder="Cole a API Key do AdsPower aqui..."
                         className="w-full bg-white/[0.02] border border-white/[0.06] rounded-lg px-3 py-2 text-[10px] font-mono text-foreground outline-none focus:border-primary/30 transition-all placeholder:text-white/10"
                       />
                    </div>
                </div>
             </GlassCard>
          </div>

          {/* COLUMN 2: ACTION CENTRAL (45%) */}
          <div className="flex flex-col gap-4">
             <GlassCard delay={0.3} className="p-4 flex flex-col flex-1 min-h-[500px]">
                <div className="flex items-center justify-between mb-4">
                   <div className="flex flex-col">
                      <h2 className="text-[11px] font-black text-foreground uppercase tracking-[0.2em]">Seleção de Perfis</h2>
                      <div className="flex items-center gap-2 mt-1">
                        <div className={`w-1.5 h-1.5 rounded-full ${isAgentConnected ? "bg-emerald-500 shadow-[0_0_8px_#10b981]" : "bg-red-500"}`} />
                        <span className="text-[8px] font-bold text-white/30 uppercase tracking-widest">
                          {isAgentConnected ? "Motor Conectado" : "Motor Desconectado"}
                        </span>
                      </div>
                   </div>
                   <button 
                     onClick={() => setIsPickerOpen(true)}
                     className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/5 rounded-lg text-[9px] font-black text-primary uppercase tracking-widest transition-all"
                   >
                     {selectedProfiles.length > 0 ? "EDITAR SELEÇÃO" : "SELECIONAR PERFIS"}
                   </button>
                </div>

                <div className="flex-1 overflow-y-auto mb-4 bg-black/20 border border-white/5 rounded-xl p-3 hide-scrollbar">
                   {selectedProfiles.length === 0 ? (
                     <div className="h-full flex flex-col items-center justify-center text-center opacity-20">
                        <Users className="w-8 h-8 mb-3" />
                        <p className="text-[10px] font-black uppercase tracking-[0.2em]">Nenhum perfil na fila</p>
                        <p className="text-[8px] mt-1 italic uppercase font-bold">Inicie selecionando quem vai aquecer hoje</p>
                     </div>
                   ) : (
                     <div className="grid grid-cols-2 gap-2">
                        {selectedProfiles.map(p => (
                          <div key={p.id} className="flex items-center justify-between p-2 bg-white/[0.03] border border-white/5 rounded-lg group/item">
                             <div className="flex flex-col min-w-0">
                                <span className="text-[10px] font-bold text-foreground truncate">{p.name}</span>
                                <span className="text-[8px] font-mono text-white/20 uppercase">{p.tag}</span>
                             </div>
                             <button 
                               onClick={() => toggleProfile(p)}
                               className="p-1 text-muted-foreground hover:text-destructive opacity-0 group-hover/item:opacity-100 transition-all"
                             >
                               <CloseIcon className="w-3 h-3" />
                             </button>
                          </div>
                        ))}
                     </div>
                   )}
                </div>

                <div className="pt-2">
                   <button
                     onClick={isActive ? handleStop : handleStart}
                     disabled={!profileIds.length && !isActive}
                     className={`w-full py-6 rounded-xl font-display font-black text-sm uppercase tracking-[0.3em] transition-all relative overflow-hidden group
                       ${isActive 
                         ? "bg-transparent border border-destructive/50 text-destructive hover:bg-destructive/5" 
                         : "bg-primary text-primary-foreground shadow-[0_0_30px_rgba(255,69,0,0.4)] hover:shadow-[0_0_50px_rgba(255,69,0,0.6)] hover:-translate-y-1 disabled:opacity-30 disabled:grayscale disabled:cursor-not-allowed"
                       }
                     `}
                   >
                     {isActive ? (
                        <span className="flex items-center justify-center gap-2">
                          <CloseIcon className="w-4 h-4" /> PARAR MOTOR
                        </span>
                     ) : (
                        <span className="fill-current flex items-center justify-center gap-2">
                           <Play className="w-4 h-4 fill-current" /> INICIALIZAR MOTOR
                        </span>
                     )}
                     <div className="absolute inset-x-0 bottom-0 h-1 bg-white/20 scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
                   </button>
                   {isActive && (
                      <div className="mt-3 py-2 px-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center justify-center gap-2">
                         <Activity className="w-3 h-3 text-emerald-500 animate-pulse" />
                         <span className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">Processando Ciclos de Elite...</span>
                      </div>
                   )}
                </div>

                {/* STATS GRID COMPACT */}
                <div className="mt-6 grid grid-cols-2 gap-3">
                   <StatCard 
                     label="Ações Realizadas" 
                     value={(totalLikes + totalComments + totalReels).toLocaleString()} 
                     subValue="Totais"
                     icon={TrendingUp} 
                     delay={0.1}
                   />
                   <StatCard 
                     label="Perfis Ativos" 
                     value={profileIds.length.toLocaleString()} 
                     subValue={isActive ? "Em execução" : "Standby"}
                     icon={Users} 
                     delay={0.2}
                   />
                   <StatCard 
                     label="Uptime Cloud" 
                     value="99.9%" 
                     subValue="Conectado"
                     icon={Cloud} 
                     delay={0.3}
                   />
                   <StatCard 
                     label="Agendamentos" 
                     value={schedulerStatus?.pending_sessions ?? "0"} 
                     subValue={schedulerActive ? `${schedulerStatus?.total_sessions ?? 0} sessões hoje` : "Desativado"}
                     icon={Calendar} 
                     delay={0.4}
                   />
                </div>
             </GlassCard>
          </div>

          {/* COLUMN 3: MONITORING (30%) */}
          <div className="flex flex-col gap-4">
             <GlassCard delay={0.4} className="p-4 flex flex-col h-[280px]">
                <div className="flex items-center justify-between mb-4">
                   <h2 className="text-[10px] font-black text-foreground uppercase tracking-[0.2em] flex items-center gap-2">
                     <ListFilter className="w-3 h-3 text-primary" />
                     Fila do Motor
                   </h2>
                   <span className="text-[8px] font-bold text-white/30 uppercase tracking-widest">{profileIds.length} Ativos</span>
                </div>
                <div className="overflow-y-auto flex-1 hide-scrollbar">
                  <ExecutionList 
                    profiles={profileIds}
                    currentProfile={currentProfile}
                    results={safeResults}
                  />
                </div>
             </GlassCard>

             <GlassCard delay={0.5} className="p-4 flex flex-col h-[320px]">
                <div className="flex justify-between items-center mb-4">
                   <h2 className="text-[10px] font-black text-primary uppercase tracking-[0.2em] flex items-center gap-2">
                     <Zap className="w-3 h-3" />
                     Log Console
                   </h2>
                   <div className="flex gap-1">
                      <div className="w-1 h-1 rounded-full bg-white/20" />
                      <div className="w-1 h-1 rounded-full bg-white/20" />
                      <div className="w-1 h-1 rounded-full bg-white/20" />
                   </div>
                </div>
                <div className="flex-1 overflow-hidden rounded-lg bg-black/40 border border-white/5">
                  <LogTerminal isActive={isActive} liveLogs={logs} />
                </div>
             </GlassCard>
          </div>
        </div>

        {/* BOTTOM: Cloud Status (minimal) */}
        <div className="mt-8 flex items-center gap-2 opacity-30 hover:opacity-60 transition-opacity">
           <div className={`w-1.5 h-1.5 rounded-full ${cloudConnected ? 'bg-emerald-500 shadow-[0_0_6px_#10b981]' : 'bg-red-500/50'}`} />
           <span className="text-[7px] font-black text-white/20 uppercase tracking-widest">
             {cloudConnected ? 'CLOUD CONECTADO' : 'CLOUD OFFLINE'}
           </span>
        </div>
      </main>

      {/* Profile Selection Modal */}
      <AnimatePresence>
        {isPickerOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={() => setIsPickerOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-card border border-border/50 rounded-2xl p-8 w-full max-w-2xl shadow-2xl relative"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                <div>
                  <h2 className="font-display text-xl font-black text-foreground uppercase tracking-tight">Selecionar Perfis</h2>
                  <p className="text-xs text-muted-foreground mt-1">Escolha quais perfis entrarão na fila de aquecimento</p>
                </div>
                
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/30" />
                    <input 
                      type="text"
                      placeholder="Buscar..."
                      value={pickerSearch}
                      onChange={(e) => setPickerSearch(e.target.value)}
                      className="bg-white/[0.03] border border-white/5 rounded-full pl-10 pr-6 py-2 text-[10px] focus:outline-none focus:border-primary/30 w-48 transition-all"
                    />
                  </div>
                  <button onClick={() => setIsPickerOpen(false)} className="p-2 hover:bg-white/5 rounded-full text-muted-foreground transition-colors">
                    <CloseIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between mb-4 px-2">
                <button 
                  onClick={selectAllProfiles}
                  className="text-[10px] font-black text-primary hover:underline uppercase tracking-widest flex items-center gap-2"
                >
                  <ListFilter className="w-3 h-3" />
                  {selectedProfiles.length === savedProfiles.length ? "DESELECIONAR TUDO" : "SELECIONAR TUDO"}
                </button>
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                  {selectedProfiles.length} selecionados
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[400px] overflow-y-auto pr-2 hide-scrollbar py-2">
                {savedProfiles.length === 0 ? (
                  <div className="col-span-full py-12 text-center opacity-30">
                    <p className="text-xs font-bold uppercase tracking-widest">Nenhum perfil salvo.</p>
                    <button onClick={() => {
                      setIsPickerOpen(false);
                      navigate("/profiles");
                    }} className="mt-2 text-primary text-[10px] font-black underline">CADASTRAR PERFIS</button>
                  </div>
                ) : (
                  filteredSaved.map(p => {
                    const isSelected = selectedProfiles.find(sp => sp.id === p.id);
                    return (
                      <button
                        key={p.id}
                        onClick={() => toggleProfile(p)}
                        className={`group flex items-center gap-4 p-4 rounded-2xl border transition-all text-left relative overflow-hidden
                          ${isSelected 
                            ? "bg-primary/[0.05] border-primary/40 shadow-[0_0_15px_rgba(240,90,40,0.1)]" 
                            : "bg-white/[0.02] border-white/5 hover:border-white/10"
                          }
                        `}
                      >
                        <div className={`w-5 h-5 rounded-full border flex items-center justify-center transition-all
                          ${isSelected ? "bg-primary border-primary" : "border-white/10 bg-white/5"}
                        `}>
                          {isSelected && <Check className="w-3 h-3 text-primary-foreground stroke-[4]" />}
                        </div>

                        <div className="flex-1 flex flex-col min-w-0">
                          <span className={`font-bold text-xs truncate mb-0.5 ${isSelected ? "text-primary" : "text-foreground"}`}>{p.name}</span>
                          <div className="flex items-center gap-2">
                            <code className="text-[9px] text-muted-foreground font-mono bg-white/[0.03] px-1.5 py-0.5 rounded-md lowercase">{p.adsPowerId}</code>
                            <span className="text-[8px] font-black text-white/20 uppercase tracking-tighter">{p.tag}</span>
                          </div>
                        </div>

                        {isSelected && (
                          <motion.div 
                            layoutId="check-glow"
                            className="absolute inset-0 bg-primary/5 pointer-events-none"
                          />
                        )}
                      </button>
                    )
                  })
                )}
              </div>

              <div className="mt-8 flex justify-end">
                <button 
                  onClick={() => setIsPickerOpen(false)}
                  className="px-8 py-3 rounded-full bg-primary text-primary-foreground font-display font-black text-[10px] uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(240,90,40,0.3)] hover:shadow-[0_0_30px_rgba(240,90,40,0.5)] transition-all hover:-translate-y-0.5"
                >
                  CONCLUIR SELEÇÃO
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Index;
