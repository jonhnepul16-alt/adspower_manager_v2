import { LucideIcon } from "lucide-react";
import GlassCard from "./GlassCard";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  subValue?: string;
  delay?: number;
}

const StatCard = ({ icon: Icon, label, value, subValue, delay = 0 }: StatCardProps) => {
  return (
    <GlassCard delay={delay} className="flex flex-col justify-between min-h-[140px] p-6 group hover:border-primary/30 transition-all">
      <div className="flex justify-between items-start mb-4">
        <div className="w-10 h-10 rounded-full bg-primary/5 flex items-center justify-center border border-white/5">
           <Icon className="w-5 h-5 text-primary" />
        </div>
        <span className="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] bg-white/[0.03] px-2 py-1 rounded-full">{label}</span>
      </div>
      <div>
        <h3 className="text-4xl font-display font-black text-foreground tracking-tight">{value}</h3>
        {subValue && (
          <p className="text-[10px] font-bold mt-1 text-primary uppercase tracking-widest">{subValue}</p>
        )}
      </div>
    </GlassCard>
  );
};

export default StatCard;
