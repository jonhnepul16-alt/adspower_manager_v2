import { useState, useEffect, useRef } from "react";
import { 
  Users, Heart, PlaySquare, MessageSquare, 
  Terminal, Activity, Zap, Layers, 
  Play, Square, Cpu, ShieldCheck, Sparkles, Command, Ghost
} from "lucide-react";
import { Card, CardHeader, StatCard, ModeButton, 
  Button, Textarea, StatusBadge 
} from "./components/ui";
import { cn } from "./lib/utils";
import { fetchStatus, startWarmup, stopWarmup } from "./lib/api";

interface ProfileResult {
  ok: boolean;
  curtidas_feed?: number;
  reels_assistidos?: number;
  postagem?: boolean;
}

export default function App() {
  const [profileIds, setProfileIds] = useState("");
  const [selectedMode, setSelectedMode] = useState("1");
  const [isRunning, setIsRunning] = useState(false);
  const [currentProfile, setCurrentProfile] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [results, setResults] = useState<Record<string, ProfileResult>>({});

  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const check = async () => {
      try {
        const status = await fetchStatus();
        setIsRunning(status.is_running);
        setCurrentProfile(status.current_profile);
        setLogs(status.logs);
        setResults(status.results);
      } catch (err) {
        console.error("Status check failed", err);
      }
    };
    check();
    const interval = setInterval(check, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleStart = async () => {
    const ids = profileIds.split("\n").map(s => s.trim()).filter(Boolean);
    if (!ids.length) return;
    try {
      await startWarmup(ids, selectedMode);
    } catch (err) {
      console.error(err);
    }
  };

  const handleStop = async () => {
    try { await stopWarmup(); } catch (err) { console.error(err); }
  };

  // Aggregated Stats
  const totalLikes = Object.values(results).reduce((acc, r) => acc + (r.curtidas_feed || 0), 0);
  const totalReels = Object.values(results).reduce((acc, r) => acc + (r.reels_assistidos || 0), 0);
  const totalPosts = Object.values(results).reduce((acc, r) => acc + (r.postagem ? 1 : 0), 0);
  const totalProfilesInput = profileIds.split("\n").filter(s => s.trim()).length;

  return (
    <div className="min-h-screen bg-[#020408] bg-mesh-soft p-12 lg:p-20 flex flex-col gap-12 lg:gap-16 selection:bg-blue-electric/20">
      
      {/* Header */}
      <header className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-6">
          <div className="w-14 h-14 bg-gradient-to-br from-blue-electric to-cyan-500 rounded-2xl flex items-center justify-center shadow-[0_0_30px_rgba(59,130,246,0.4)] ring-1 ring-white/20">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-3xl font-black text-white leading-none font-display tracking-tight">Vexel <span className="text-blue-electric">Contigência</span></h1>
            <p className="text-[10px] text-zinc-600 font-black uppercase tracking-[0.4em] mt-2.5 flex items-center gap-2">
               <Command className="w-3 h-3" /> Facebook Warmup Bot — v3.4.1 Stable
            </p>
          </div>
        </div>
        <div className="flex items-center gap-6">
           <StatusBadge label={isRunning ? "Thread Ativa" : "Sistema Ocioso"} active={isRunning} />
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        <StatCard icon={Users} value={totalProfilesInput} label="Perfis Carregados" />
        <StatCard icon={Heart} value={totalLikes} label="Likes Gerados" />
        <StatCard icon={PlaySquare} value={totalReels} label="Reels Assistidos" />
        <StatCard icon={MessageSquare} value={totalPosts} label="Status Publicados" />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-12 gap-12 flex-1">
        
        {/* Left Column (Automation Inputs) */}
        <div className="col-span-12 lg:col-span-5 flex flex-col gap-10">
          
          <Card className="flex-1 shadow-2xl bg-white/[0.01]">
            <CardHeader title="Account Profile Injection" icon={Cpu} />
            <Textarea 
              className="flex-1 min-h-[180px] bg-black/40 border-white/[0.03] text-base"
              placeholder="Paste AdsPower IDs (one per line)...&#10;&#10;Ex: j8a1z4, jm14x2, kc11w3"
              value={profileIds}
              onChange={(e: any) => setProfileIds(e.target.value)}
              disabled={isRunning}
            />
            <div className="mt-8 flex items-center justify-between px-2">
               <p className="text-[10px] font-black text-blue-electric/60 uppercase tracking-widest flex items-center gap-2">
                  <Sparkles className="w-3 h-3" /> Auto-Detection Active
               </p>
               <span className="text-[10px] font-black text-zinc-700 uppercase tracking-widest leading-none">
                  {totalProfilesInput} Target(s) Ready
               </span>
            </div>
          </Card>

          <Card className="bg-white/[0.01]">
            <CardHeader title="Execution Flow Strategy" icon={Zap} />
            <div className="grid grid-cols-3 gap-6">
              <ModeButton 
                icon={Zap} 
                title="Rápido" 
                duration="15 min" 
                active={selectedMode === "1"} 
                onClick={() => setSelectedMode("1")} 
              />
              <ModeButton 
                icon={Activity} 
                title="Padrão" 
                duration="45 min" 
                active={selectedMode === "2"} 
                onClick={() => setSelectedMode("2")} 
              />
              <ModeButton 
                icon={Layers} 
                title="Intenso" 
                duration="90 min" 
                active={selectedMode === "3"} 
                onClick={() => setSelectedMode("3")} 
              />
            </div>
          </Card>

          <div className="flex gap-6 pt-2">
            <Button 
              className="flex-1 py-6 shadow-2xl" 
              onClick={handleStart} 
              disabled={isRunning || !profileIds}
            >
              <Play className="w-4 h-4 fill-current mr-2" /> Start Bulk Warmup
            </Button>
            <Button 
              className="py-6 px-10" 
              variant="danger" 
              onClick={handleStop} 
              disabled={!isRunning}
            >
              <Square className="w-4 h-4 fill-current" />
            </Button>
          </div>

        </div>

        {/* Right Column (Monitoring & Output) */}
        <div className="col-span-12 lg:col-span-7 flex flex-col gap-10">
          
          <Card className="flex-[3] bg-white/[0.01] overflow-hidden relative group">
            <div className="absolute inset-0 bg-blue-electric/[0.02] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
            <CardHeader title="Real-Time Engine Monitor" icon={Activity} />
            <div className="flex-1 flex flex-col items-center justify-center p-12">
              {isRunning && currentProfile ? (
                 <div className="flex flex-col items-center gap-8">
                    <div className="w-24 h-24 rounded-full bg-blue-electric/5 flex items-center justify-center border border-blue-electric/20 relative">
                       <Cpu className="w-10 h-10 text-blue-electric animate-spin" />
                       <div className="absolute inset-0 bg-blue-electric/20 rounded-full blur-2xl animate-pulse" />
                    </div>
                    <div className="text-center">
                       <p className="text-[10px] font-black text-blue-electric uppercase tracking-[0.3em] mb-2">Analyzing Profile Core</p>
                       <p className="text-3xl font-black text-white font-display tracking-tighter">{currentProfile}</p>
                    </div>
                 </div>
              ) : (
                <div className="flex flex-col items-center gap-4 opacity-20 grayscale">
                   <Ghost className="w-16 h-16 text-zinc-500" />
                   <p className="text-xs font-black uppercase tracking-[0.4em] text-zinc-600">Engine Queue Idle</p>
                </div>
              )}
            </div>
          </Card>

          <Card className="flex-[2] bg-white/[0.01] overflow-hidden">
            <div className="flex items-center justify-between mb-8 border-b border-white/[0.03] pb-6">
               <div className="flex items-center gap-3">
                  <Terminal className="w-4 h-4 text-zinc-600" />
                  <h3 className="text-sm font-bold text-white/90 font-display">Log Output Stream</h3>
               </div>
               <div className="w-2 h-2 rounded-full bg-blue-electric/40 animate-pulse" />
            </div>
            <div className="flex-1 overflow-y-auto font-mono text-[11px] text-zinc-500 pr-4 custom-scrollbar">
              {logs.length === 0 ? (
                <div className="h-full flex items-center justify-center italic opacity-30">
                  <p>Awaiting engine initial handshake...</p>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {logs.map((line, i) => {
                    let color = "text-zinc-600";
                    if (line.includes("✓")) color = "text-emerald-400 font-bold";
                    else if (line.includes("✗")) color = "text-red-400 font-bold";
                    else if (line.includes("▶")) color = "text-blue-electric font-black";
                    
                    return (
                      <div key={i} className={cn("whitespace-pre-wrap leading-relaxed border-l border-white/[0.05] pl-4", color)}>
                        {line}
                      </div>
                    );
                  })}
                  <div ref={logsEndRef} />
                </div>
              )}
            </div>
          </Card>

        </div>

      </div>

    </div>
  );
}
