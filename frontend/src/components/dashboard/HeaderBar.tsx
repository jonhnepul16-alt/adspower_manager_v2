import { Shield } from "lucide-react";
import { motion } from "framer-motion";

interface HeaderBarProps {
  isActive: boolean;
  isAgentConnected?: boolean;
}

const HeaderBar = ({ isActive, isAgentConnected = false }: HeaderBarProps) => {

  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex items-center justify-between"
    >
      <div className="flex items-center gap-4">
        <div className="relative p-3 rounded-2xl bg-primary/10 border border-primary/20">
          <Shield className="w-7 h-7 text-primary" />
          <div className="absolute inset-0 rounded-2xl bg-primary/10 breathe -z-10" />
        </div>
        <div>
          <h1 className="font-display text-xl font-bold tracking-tight text-foreground">
            Vexel Contigência
          </h1>
          <p className="text-xs text-muted-foreground font-body">
            Facebook Profile Warmup Engine
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Agent Connection Status */}
        <div className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full border transition-all duration-500 ${
          isAgentConnected
            ? "border-primary/30 bg-primary/5 text-primary"
            : "border-destructive/20 bg-destructive/5 text-destructive/60"
        }`}>
          <div className="relative flex h-1.5 w-1.5">
            {isAgentConnected && (
               <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-40" />
            )}
            <span className={`relative inline-flex rounded-full h-1.5 w-1.5 ${
              isAgentConnected ? "bg-primary" : "bg-destructive/40"
            }`} />
          </div>
          <span className="text-[10px] font-display font-bold uppercase tracking-widest">
            {isAgentConnected ? "Cloud Link Active" : "Local Agent Offline"}
          </span>
        </div>

        {/* Operation Status */}
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full border ${
          isActive
            ? "border-emerald-500/30 bg-emerald-500/10"
            : "border-border bg-muted/30"
        }`}>
          <span className={`relative flex h-2.5 w-2.5`}>
            {isActive && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            )}
            <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
              isActive ? "bg-emerald-400" : "bg-muted-foreground/40"
            }`} />
          </span>
          <span className={`text-xs font-body font-medium ${
            isActive ? "text-emerald-400" : "text-muted-foreground"
          }`}>
            {isActive ? "Active" : "Idle"}
          </span>
        </div>
      </div>
    </motion.header>
  );
};

export default HeaderBar;
