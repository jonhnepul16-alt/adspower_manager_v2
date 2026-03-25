import { useEffect, useState } from "react";
import { Users, Heart, Play, MessageSquare } from "lucide-react";
import { motion } from "framer-motion";
import HeaderBar from "@/components/dashboard/HeaderBar";
import StatCard from "@/components/dashboard/StatCard";
import GlassCard from "@/components/dashboard/GlassCard";
import StrategySelector from "@/components/dashboard/StrategySelector";
import EngineCore from "@/components/dashboard/EngineCore";
import LogTerminal from "@/components/dashboard/LogTerminal";
import { fetchStatus, startWarmup, stopWarmup } from "@/lib/api";

type ProfileResult = {
  ok: boolean;
  curtidas_feed?: number;
  reels_assistidos?: number;
  postagem?: boolean;
};

const Index = () => {
  const [isActive, setIsActive] = useState(false);
  const [isAgentConnected, setIsAgentConnected] = useState(false);
  const [profiles, setProfiles] = useState("");
  const [selectedMode, setSelectedMode] = useState("1");
  const [logs, setLogs] = useState<string[]>([]);
  const [results, setResults] = useState<Record<string, ProfileResult>>({});
  const [currentProfile, setCurrentProfile] = useState<string | null>(null);

  useEffect(() => {
    const check = async () => {
      try {
        const status = await fetchStatus("default");
        setIsActive(status.is_running);
        setIsAgentConnected(status.agent_connected);
        setLogs(status.logs);
        setResults(status.results);
        setCurrentProfile(status.current_profile);
      } catch (err) {
        console.error("Failed to fetch status", err);
      }
    };

    check();
    const interval = setInterval(check, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    const ids = profiles.split("\n").map(s => s.trim()).filter(Boolean);
    if (!ids.length) return;
    try {
      await startWarmup(ids, selectedMode);
      setIsActive(true);
    } catch (err) {
      console.error(err);
    }
  };

  const handleStop = async () => {
    try {
      await stopWarmup();
      setIsActive(false);
    } catch (err) {
      console.error(err);
    }
  };

  const totalLikes = Object.values(results).reduce((acc, r) => acc + (r.curtidas_feed || 0), 0);
  const totalReels = Object.values(results).reduce((acc, r) => acc + (r.reels_assistidos || 0), 0);
  const totalPosts = Object.values(results).reduce((acc, r) => acc + (r.postagem ? 1 : 0), 0);
  const totalProfilesCount = profiles.split("\n").filter(Boolean).length;

  return (
    <div className="min-h-screen p-4 md:p-6 lg:p-8 max-w-[1440px] mx-auto flex flex-col gap-6">
      <HeaderBar isActive={isActive} isAgentConnected={isAgentConnected} />


      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Users} label="Perfis Carregados" value={totalProfilesCount.toString()} delay={0.1} />
        <StatCard icon={Heart} label="Likes Gerados" value={totalLikes.toString()} delay={0.15} />
        <StatCard icon={Play} label="Reels Assistidos" value={totalReels.toString()} delay={0.2} />
        <StatCard icon={MessageSquare} label="Status Publicados" value={totalPosts.toString()} delay={0.25} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
        <div className="lg:col-span-5 flex flex-col gap-4">
          <GlassCard delay={0.3}>
            <h2 className="font-display font-semibold text-sm text-foreground mb-3 uppercase tracking-widest text-[10px] opacity-60">
               Direct Injection
            </h2>
            <textarea
              value={profiles}
              onChange={(e) => setProfiles(e.target.value)}
              placeholder="Ex: 1000123456...&#10;One ID per line"
              rows={5}
              className="w-full bg-muted/30 border border-border rounded-2xl px-6 py-4 text-sm font-mono text-foreground placeholder:text-muted-foreground/30 resize-none focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/20 transition-all custom-scrollbar"
            />
            <div className="flex items-center justify-between mt-3 px-1">
               <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest leading-none">
                  {totalProfilesCount} Targets Detected
               </p>
               <div className="w-1.5 h-1.5 rounded-full bg-primary/40 animate-pulse" />
            </div>
          </GlassCard>

          <GlassCard delay={0.35}>
            <h2 className="font-display font-semibold text-sm text-foreground mb-4 uppercase tracking-widest text-[10px] opacity-60">
              Warmup Strategy Control
            </h2>
            <StrategySelector value={selectedMode} onChange={setSelectedMode} />
          </GlassCard>

          <GlassCard delay={0.4} hover={false}>
            <div className="flex gap-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleStart}
                disabled={isActive || !profiles}
                className={`flex-1 py-4 rounded-2xl font-display font-bold text-xs uppercase tracking-[0.2em] transition-all shimmer ${
                  isActive
                    ? "bg-muted/50 text-muted-foreground cursor-not-allowed"
                    : "bg-gradient-to-r from-primary to-accent text-primary-foreground glow-blue"
                }`}
              >
                {isActive ? "Engine Engaged" : "Initialize Engine"}
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleStop}
                disabled={!isActive}
                className={`px-8 py-4 rounded-2xl font-display font-bold text-xs border transition-all ${
                  !isActive
                    ? "border-border text-muted-foreground/20 cursor-not-allowed"
                    : "border-destructive/40 text-destructive hover:bg-destructive/10"
                }`}
              >
                Stop
              </motion.button>
            </div>
          </GlassCard>
        </div>

        <div className="lg:col-span-7 flex flex-col gap-4">
          <GlassCard delay={0.3}>
            <h2 className="font-display font-semibold text-sm text-foreground mb-1 uppercase tracking-widest text-[10px] opacity-60">
               Core Monitor
            </h2>
            <EngineCore isActive={isActive} currentProfile={currentProfile} />
          </GlassCard>

          <GlassCard delay={0.35} className="flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-4 mt-2">
               <h2 className="font-display font-semibold text-sm text-foreground uppercase tracking-widest text-[10px] opacity-60">
                  Automation Output logs
               </h2>
               <div className="w-2 h-2 rounded-full bg-emerald-500/40 animate-pulse" />
            </div>
            <LogTerminal isActive={isActive} liveLogs={logs} />
          </GlassCard>
        </div>
      </div>
    </div>
  );
};

export default Index;
