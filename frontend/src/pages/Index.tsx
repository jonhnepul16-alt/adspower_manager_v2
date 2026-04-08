import { useEffect, useState } from "react";
import { Users, Heart, Play, MessageSquare, Zap } from "lucide-react";
import { motion } from "framer-motion";
import HeaderBar from "@/components/dashboard/HeaderBar";
import GlassCard from "@/components/dashboard/GlassCard";
import StrategySelector from "@/components/dashboard/StrategySelector";
import LogTerminal from "@/components/dashboard/LogTerminal";
import SchedulerConfig from "@/components/dashboard/SchedulerConfig";
import Sidebar from "@/components/dashboard/Sidebar";
import { fetchStatus, startWarmup, stopWarmup, updateScheduler } from "@/lib/api";
import { toast } from "sonner";


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
  const [isAgentConnected, setIsAgentConnected] = useState(false);
  const [profiles, setProfiles] = useState("");
  const [selectedMode, setSelectedMode] = useState("1");
  const [logs, setLogs] = useState<string[]>([]);
  const [results, setResults] = useState<Record<string, ProfileResult>>({});
  const [schedulerConfig, setSchedulerConfig] = useState<any>(null);
  const [schedulerStatus, setSchedulerStatus] = useState<any>(null);
  const [schedulerActive, setSchedulerActive] = useState(false);
  const [currentProfile, setCurrentProfile] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("vexel_api_key") || "default");

  const safeResults = results ?? {};

  // Persist API Key changes
  useEffect(() => {
    localStorage.setItem("vexel_api_key", apiKey);
  }, [apiKey]);

  useEffect(() => {
    const check = async () => {
      try {
        const status = await fetchStatus(apiKey);
        if (!status) return;
        setIsActive(status.is_running ?? false);
        setIsAgentConnected(status.agent_connected ?? false);
        // Logs: pull real messages from backend
        if (Array.isArray(status.logs)) setLogs(status.logs);
        setResults(status.results ?? {});
        const cfg = status.scheduler_config ?? null;
        setSchedulerConfig(cfg);
        setSchedulerStatus(status.scheduler_status ?? null);
        setCurrentProfile(status.current_profile ?? null);
        // Sync scheduler active state from server
        if (cfg && cfg.active !== undefined) {
          setSchedulerActive(!!cfg.active);
        }
      } catch (err) {
        console.error("Failed to fetch status", err);
      }
    };

    check();
    const interval = setInterval(check, 2000);
    return () => clearInterval(interval);
  }, [apiKey]);

  const handleStart = async () => {
    const ids = profiles.split("\n").map(s => s.trim()).filter(Boolean);
    if (!ids.length) return;
    try {
      await startWarmup(ids, selectedMode, apiKey);
      setIsActive(true);
      toast.success("Comando de inicialização enviado!");
    } catch (err) {
      console.error(err);
      toast.error("Erro ao iniciar: " + (err instanceof Error ? err.message : "Erro desconhecido"));
    }
  };

  const handleStop = async () => {
    try {
      await stopWarmup(apiKey);
      setIsActive(false);
      toast.success("Comando de parada enviado!");
    } catch (err) {
      console.error(err);
      toast.error("Erro ao parar: " + (err instanceof Error ? err.message : "Erro desconhecido"));
    }
  };

  const handleUpdateScheduler = async (config: any) => {
    const ids = profiles.split("\n").map(s => s.trim()).filter(Boolean);
    try {
      await updateScheduler(apiKey, { ...config, profile_ids: ids });
      toast.success("Agendamento sincronizado!");
    } catch (err) {
      toast.error("Erro ao atualizar agendamento");
    }
  };

  const handleToggleScheduler = async () => {
    const newActive = !schedulerActive;
    setSchedulerActive(newActive);
    const ids = profiles.split("\n").map(s => s.trim()).filter(Boolean);
    const cfg = { ...(schedulerConfig || {}), active: newActive, profile_ids: ids };
    try {
      await updateScheduler(apiKey, cfg);
      toast.success(newActive ? "Agendamento ATIVADO!" : "Agendamento PAUSADO!");
    } catch (err) {
      setSchedulerActive(!newActive); // rollback on error
      toast.error("Erro ao alterar estado do agendamento");
    }
  };

  const totalLikes = Object.values(safeResults).reduce((acc, r) => acc + (r.curtidas_feed || 0) + (r.reacoes_dadas || 0), 0);
  const totalComments = Object.values(safeResults).reduce((acc, r) => acc + (r.comentarios_feitos || 0), 0);
  const totalReels = Object.values(safeResults).reduce((acc, r) => acc + (r.reels_assistidos || 0), 0);
  const totalGroupsFriends = Object.values(safeResults).reduce((acc, r) => acc + (r.grupos_visitados || 0) + (r.amigos_adicionados || 0), 0);
  const totalPosts = Object.values(safeResults).reduce((acc, r) => acc + (r.postagem ? 1 : 0), 0);
  const totalProfilesCount = profiles.split("\n").filter(Boolean).length;

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col p-6 lg:px-12 max-w-[1600px] overflow-y-auto">
        
        <HeaderBar
          isActive={isActive}
          isAgentConnected={isAgentConnected}
          apiKey={apiKey}
          onApiKeyChange={setApiKey}
        />

        {/* Hero Section */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mt-2 mb-8">
          <div className="w-full relative flex flex-col items-center text-center">
            {/* Logo Hover Laser Effect */}
            <div className="group cursor-pointer relative w-36 h-24 mb-6 bg-black mix-blend-screen overflow-hidden flex items-center justify-center">
               <img src="/logo.png" alt="Vexel Pulse" className="absolute w-full h-full object-contain filter invert opacity-70 group-hover:opacity-100 transition-opacity duration-700" />
               <div className="absolute top-0 w-[120%] h-full bg-gradient-to-r from-transparent via-amber-400 to-transparent mix-blend-multiply skew-x-[-20deg] left-[-150%] group-hover:left-[200%] transition-[left] duration-700 ease-out" />
            </div>

            <div className="flex items-center justify-center gap-2 mb-3">
              <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-emerald-500 animate-pulse' : 'bg-muted-foreground'}`} />
              <span className={`text-[10px] font-bold tracking-widest uppercase ${isActive ? 'text-emerald-500' : 'text-muted-foreground'}`}>
                {isActive ? 'MOTOR ATIVO' : 'MOTOR EM ESPERA'}
              </span>
            </div>
            <h1 className="font-display text-4xl lg:text-5xl font-black text-foreground tracking-tight leading-none mb-3">
              Motor de Aquecimento <br/>de Perfis
            </h1>
            <p className="text-sm text-foreground/60 font-medium max-w-md mx-auto">
              Simulação de atividades automatizadas inteligentes para perfis de elite.
            </p>
          </div>
          
          <div className="mt-6 lg:mt-0 flex flex-row items-center gap-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleStart}
              disabled={isActive || !profiles}
              className={`flex items-center justify-center gap-2 px-6 py-3 rounded-full font-display font-bold text-[10px] uppercase tracking-[0.2em] transition-all
                  ${isActive || !profiles 
                    ? 'opacity-40 cursor-not-allowed bg-muted text-muted-foreground' 
                    : "bg-primary text-primary-foreground shadow-[0_0_20px_-5px_rgba(251,191,36,0.4)] hover:shadow-[0_0_30px_0px_rgba(251,191,36,0.6)]"
                  }
              `}
            >
              <Zap className="w-3.5 h-3.5" />
              INICIALIZAR MOTOR
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleStop}
              disabled={!isActive}
              className={`flex items-center justify-center gap-2 px-6 py-3 rounded-full font-display font-bold text-[10px] uppercase tracking-[0.2em] transition-all border
                  ${!isActive 
                    ? 'opacity-20 cursor-not-allowed border-border text-muted-foreground' 
                    : "border-destructive/50 text-destructive hover:bg-destructive/10"
                  }
              `}
            >
              <div className="w-2 h-2 rounded-full bg-destructive animate-pulse mr-1" />
              DESLIGAR MOTOR
            </motion.button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-5">
           {/* Global Status Card */}
           <div className="md:col-span-1 glass p-6 flex flex-col justify-between min-h-[220px]">
              <div className="flex justify-between items-start mb-6">
                 <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <Users className="w-5 h-5 text-primary" />
                 </div>
                 <span className="text-[9px] font-bold tracking-widest text-muted-foreground bg-card px-2 py-1 border border-border/50 rounded-full uppercase">Status Global</span>
              </div>
              <div>
                 <h3 className="font-display text-5xl font-bold tracking-tight text-foreground mb-1">{totalProfilesCount.toLocaleString()}</h3>
                 <p className="text-sm text-foreground/60 mb-6">Total de Perfis Ativos</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                 <div className="bg-card border border-border/40 rounded-xl p-3">
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Amigos & Grupos</p>
                    <p className="font-mono text-emerald-500 font-bold text-sm">+{totalGroupsFriends}</p>
                 </div>
                 <div className="bg-card border border-border/40 rounded-xl p-3">
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Reels Vistos</p>
                    <p className="font-mono text-primary font-bold text-sm">{totalReels}</p>
                 </div>
              </div>
           </div>

           {/* Reactions Mini Card */}
           <div className="glass p-6 flex flex-col justify-between min-h-[220px]">
              <div className="w-10 h-10 flex items-center justify-center mb-6">
                 <Heart className="w-6 h-6 text-primary" />
              </div>
              <div className="mt-auto">
                 <h3 className="font-display text-4xl font-bold tracking-tight text-foreground mb-1">{(totalLikes/1000).toFixed(1)}K</h3>
                 <p className="text-xs font-bold text-foreground/50 uppercase tracking-widest">Reações</p>
              </div>
           </div>

           {/* Comments Mini Card */}
           <div className="glass p-6 flex flex-col justify-between min-h-[220px]">
              <div className="w-10 h-10 flex items-center justify-center mb-6">
                 <MessageSquare className="w-6 h-6 text-primary" />
              </div>
              <div className="mt-auto">
                 <h3 className="font-display text-4xl font-bold tracking-tight text-foreground mb-1">{(totalComments/1000).toFixed(1)}K</h3>
                 <p className="text-xs font-bold text-foreground/50 uppercase tracking-widest">Comentários</p>
              </div>
           </div>
        </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 flex-1">
        
        {/* Center/Left Column */}
        <div className="lg:col-span-2 flex flex-col gap-5">
           
          {/* Strategy Control */}
          <GlassCard delay={0.1} className="flex-none p-6">
            <div className="flex justify-between items-center mb-6">
               <h2 className="font-display font-bold text-lg tracking-tight text-foreground">
                 Estratégias de Aquecimento
               </h2>
               <button className="text-[10px] font-bold text-primary uppercase tracking-widest hover:text-primary/80 transition-colors">
                  Ver Perfis Ativos
               </button>
            </div>
            <StrategySelector value={selectedMode} onChange={setSelectedMode} />
            
            {/* Fake Graph Area mimicking the mock */}
            <div className="mt-6 h-40 bg-card rounded-2xl border border-border/30 relative overflow-hidden flex items-center justify-center group">
               {/* Background grid lines */}
               <div className="absolute inset-0 opacity-10 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
               <div className="z-10 flex flex-col items-center gap-2 transform transition-transform group-hover:scale-105">
                  <Play className="w-6 h-6 text-primary" />
                  <span className="text-[10px] font-bold text-primary uppercase tracking-widest">Feed em Tempo Real</span>
               </div>
            </div>
          </GlassCard>

          <GlassCard delay={0.2} className="flex-1 p-6">
            <h2 className="font-display font-bold text-lg tracking-tight text-foreground mb-4">
               Injeção Direta (IDs)
            </h2>
            <textarea
              value={profiles}
              onChange={(e) => setProfiles(e.target.value)}
              placeholder="Ex: 1000123456...&#10;Cole os IDs dos alvos aqui"
              rows={4}
              className="w-full bg-card border border-border/50 rounded-xl px-4 py-3 text-sm font-mono text-foreground placeholder:text-muted-foreground/30 resize-none focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all custom-scrollbar"
            />
          </GlassCard>

        </div>

        {/* Right Column */}
        <div className="lg:col-span-1 flex flex-col gap-5">
          <div className="glass p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-display font-bold text-lg tracking-tight text-foreground">
                Agendamento
              </h2>
              {/* Master Scheduler Toggle */}
              <div className="flex items-center gap-2">
                <span className={`text-[9px] font-bold uppercase tracking-widest ${schedulerActive ? 'text-emerald-500' : 'text-muted-foreground'}`}>
                  {schedulerActive ? 'Ativo' : 'Pausado'}
                </span>
                <button
                  onClick={handleToggleScheduler}
                  className={`w-12 h-6 rounded-full transition-colors relative flex items-center px-1 ${
                    schedulerActive ? 'bg-emerald-500' : 'bg-muted-foreground/30'
                  }`}
                >
                  <motion.div
                    animate={{ x: schedulerActive ? 24 : 0 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                    className="w-4 h-4 bg-white rounded-full shadow-sm"
                  />
                </button>
              </div>
            </div>
            <SchedulerConfig 
              config={schedulerConfig}
              status={schedulerStatus}
              onUpdate={handleUpdateScheduler}
            />
          </div>

          <GlassCard delay={0.3} className="flex-1 flex flex-col p-6 min-h-[300px]">
            <h2 className="font-display font-bold text-lg tracking-tight text-foreground mb-4">
               Logs de Automação
            </h2>
            <LogTerminal isActive={isActive} liveLogs={logs} />
          </GlassCard>
        </div>
      </div>
      </div>
    </div>
  );
};

export default Index;
