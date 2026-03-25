import { useState } from "react";
import { Users, Heart, Play, MessageSquare } from "lucide-react";
import { motion } from "framer-motion";
import HeaderBar from "@/components/dashboard/HeaderBar";
import StatCard from "@/components/dashboard/StatCard";
import GlassCard from "@/components/dashboard/GlassCard";
import StrategySelector from "@/components/dashboard/StrategySelector";
import EngineCore from "@/components/dashboard/EngineCore";
import LogTerminal from "@/components/dashboard/LogTerminal";

const Index = () => {
  const [isActive, setIsActive] = useState(false);
  const [profiles, setProfiles] = useState(
    "profile_01\nprofile_02\nprofile_03"
  );

  return (
    <div className="min-h-screen p-4 md:p-6 lg:p-8 max-w-[1440px] mx-auto flex flex-col gap-6">
      {/* Header */}
      <HeaderBar isActive={isActive} />

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Users} label="Perfis Carregados" value="12" delay={0.1} />
        <StatCard icon={Heart} label="Likes Gerados" value="1,847" delay={0.15} />
        <StatCard icon={Play} label="Reels Assistidos" value="623" delay={0.2} />
        <StatCard icon={MessageSquare} label="Status Publicados" value="89" delay={0.25} />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
        {/* Automation Panel */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          {/* Profile Injection */}
          <GlassCard delay={0.3}>
            <h2 className="font-display font-semibold text-sm text-foreground mb-3">
              Profile Injection
            </h2>
            <textarea
              value={profiles}
              onChange={(e) => setProfiles(e.target.value)}
              placeholder="Cole os perfis aqui, um por linha..."
              rows={5}
              className="w-full bg-muted/30 border border-border rounded-2xl px-4 py-3 text-sm font-mono text-foreground placeholder:text-muted-foreground/50 resize-none focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/20 transition-all"
            />
            <p className="text-xs text-muted-foreground mt-2">
              {profiles.split("\n").filter(Boolean).length} perfis detectados
            </p>
          </GlassCard>

          {/* Strategy */}
          <GlassCard delay={0.35}>
            <h2 className="font-display font-semibold text-sm text-foreground mb-3">
              Warmup Strategy
            </h2>
            <StrategySelector />
          </GlassCard>

          {/* Actions */}
          <GlassCard delay={0.4} hover={false}>
            <div className="flex gap-3">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setIsActive(true)}
                disabled={isActive}
                className={`flex-1 py-3.5 rounded-2xl font-display font-semibold text-sm transition-all shimmer ${
                  isActive
                    ? "bg-muted/50 text-muted-foreground cursor-not-allowed"
                    : "bg-gradient-to-r from-primary to-accent text-primary-foreground glow-blue"
                }`}
              >
                {isActive ? "Running..." : "Start Warmup"}
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setIsActive(false)}
                disabled={!isActive}
                className={`px-6 py-3.5 rounded-2xl font-display font-semibold text-sm border transition-all ${
                  !isActive
                    ? "border-border text-muted-foreground/40 cursor-not-allowed"
                    : "border-destructive/40 text-destructive hover:bg-destructive/10"
                }`}
              >
                Stop
              </motion.button>
            </div>
          </GlassCard>
        </div>

        {/* Engine Dashboard */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          {/* Engine Core */}
          <GlassCard delay={0.3}>
            <h2 className="font-display font-semibold text-sm text-foreground mb-1">
              Engine Core
            </h2>
            <EngineCore isActive={isActive} />
          </GlassCard>

          {/* Log Terminal */}
          <GlassCard delay={0.35} className="flex-1 flex flex-col">
            <h2 className="font-display font-semibold text-sm text-foreground mb-3">
              Log Output
            </h2>
            <LogTerminal isActive={isActive} />
          </GlassCard>
        </div>
      </div>
    </div>
  );
};

export default Index;
