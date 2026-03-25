import { type ReactNode } from "react";
import { cn } from "../lib/utils";
import { motion } from "framer-motion";

export const Card = ({ children, className }: { children: ReactNode; className?: string }) => (
  <motion.div 
    whileHover={{ y: -4, scale: 1.002 }}
    className={cn("glass-panel p-10 flex flex-col h-full", className)}
  >
    {children}
  </motion.div>
);

export const CardHeader = ({ title, icon: Icon }: { title: string; icon?: any }) => (
  <div className="flex items-center gap-4 mb-8">
    <div className="w-10 h-10 rounded-2xl bg-blue-electric/10 flex items-center justify-center border border-blue-electric/20 shadow-inner">
       {Icon && <Icon className="w-5 h-5 text-blue-electric" />}
    </div>
    <h3 className="text-base font-bold text-white/90 font-display tracking-tight">{title}</h3>
  </div>
);

export const StatCard = ({ icon: Icon, value, label }: { icon: any; value: string | number; label: string }) => (
  <motion.div 
    whileHover={{ scale: 1.02, y: -4 }}
    className="glass-panel flex items-center gap-6 p-6 flex-1 min-w-[200px]"
  >
    <div className="w-14 h-14 rounded-[1.25rem] bg-gradient-to-br from-blue-electric/20 to-cyan-500/10 flex items-center justify-center border border-white/5 shadow-inner">
      <Icon className="w-6 h-6 text-blue-electric" />
    </div>
    <div className="flex flex-col">
      <span className="text-3xl font-black text-white font-display tracking-tighter tabular-nums">{value}</span>
      <span className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mt-0.5">{label}</span>
    </div>
  </motion.div>
);

export const ModeButton = ({ 
  icon: Icon, 
  title, 
  duration, 
  active, 
  onClick 
}: { 
  icon: any; 
  title: string; 
  duration: string; 
  active?: boolean; 
  onClick: () => void;
}) => (
  <button
    onClick={onClick}
    className={cn(
      "flex-1 flex flex-col items-center justify-center p-8 rounded-[2rem] border transition-all duration-500 group relative overflow-hidden",
      active 
        ? "bg-blue-electric/5 border-blue-electric text-blue-electric shadow-[0_0_30px_rgba(59,130,246,0.2)]" 
        : "bg-white/[0.02] border-white/5 text-zinc-500 hover:border-zinc-700"
    )}
  >
    <Icon className={cn("w-7 h-7 mb-3", active ? "text-blue-electric animate-pulse" : "text-zinc-600 group-hover:text-zinc-400")} />
    <span className={cn("text-xs font-black uppercase tracking-widest", active ? "text-white" : "text-zinc-500")}>{title}</span>
    <span className="text-[10px] mt-1.5 opacity-60 font-black uppercase tracking-tighter">{duration}</span>
    {active && <div className="absolute inset-0 bg-blue-electric/5 animate-pulse" />}
  </button>
);

export const Button = ({
  children,
  variant = "primary",
  className,
  ...props
}: {
  children: ReactNode;
  variant?: "primary" | "danger" | "outline";
  className?: string;
  [key: string]: any;
}) => {
  const variants = {
    primary: "btn-electric font-black uppercase tracking-[0.2em] py-5 px-10 text-xs",
    danger: "bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 rounded-[1.5rem] font-black uppercase tracking-[0.2em] py-5 px-10 text-xs",
    outline: "bg-transparent border border-white/10 text-zinc-400 hover:bg-white/5 rounded-[1.5rem] py-5 px-10 text-xs"
  };
  
  return (
    <button
      className={cn(
        "flex items-center justify-center gap-3 transition-all duration-300 disabled:opacity-20",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};

export const Textarea = ({ className, ...props }: any) => (
  <textarea
    className={cn(
      "w-full bg-black/40 border border-white/5 rounded-[2rem] p-8 text-sm text-white placeholder-zinc-700 focus:outline-none focus:border-blue-electric/40 transition-all duration-500 resize-none leading-relaxed",
      className
    )}
    {...props}
  />
);

export const StatusBadge = ({ label, active }: { label: string; active?: boolean }) => (
  <div className={cn(
    "flex items-center gap-3 px-6 py-2.5 rounded-full border text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-500",
    active 
      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_15px_rgba(34,197,94,0.15)]" 
      : "bg-zinc-900 border-white/5 text-zinc-600 grayscale"
  )}>
    <div className={cn("w-2 h-2 rounded-full", active ? "bg-emerald-400 animate-pulse" : "bg-zinc-700")} />
    {label}
  </div>
);
