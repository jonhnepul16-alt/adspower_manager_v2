import { LucideIcon } from "lucide-react";
import GlassCard from "./GlassCard";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  delay?: number;
}

const StatCard = ({ icon: Icon, label, value, delay = 0 }: StatCardProps) => {
  return (
    <GlassCard delay={delay} className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-primary/10">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <span className="text-sm text-muted-foreground font-body">{label}</span>
      </div>
      <span className="text-3xl font-display font-bold tracking-tight tabular-nums text-foreground">
        {value}
      </span>
    </GlassCard>
  );
};

export default StatCard;
