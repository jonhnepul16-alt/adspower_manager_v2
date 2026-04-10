import { motion } from "framer-motion";

interface Props {
  data: Record<string, any>;
}

const ActionBarChart = ({ data }: Props) => {
  const profileEntries = Object.entries(data);
  // Se não houver dados, mostrar bars dummy para manter o design
  const items = profileEntries.length > 0 
    ? profileEntries.slice(-10) 
    : Array(10).fill(["-", { curtidas_feed: 0, reacoes_dadas: 0, comentarios_feitos: 0 }]);

  const maxActions = Math.max(...items.map(([_, r]: any) => 
    (r.curtidas_feed || 0) + (r.reacoes_dadas || 0) + (r.comentarios_feitos || 0)
  ), 10);

  return (
    <div className="flex items-end justify-between gap-1 h-32 w-full pt-4">
      {items.map(([pid, r]: any, i) => {
        const total = (r.curtidas_feed || 0) + (r.reacoes_dadas || 0) + (r.comentarios_feitos || 0);
        const height = (total / maxActions) * 100;
        
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
            <div className="relative w-full flex flex-col justify-end h-full">
               <motion.div
                 initial={{ height: 0 }}
                 animate={{ 
                   height: `${Math.max(height, 5)}%`,
                   opacity: i === items.length - 1 ? [0.6, 1, 0.6] : 1
                 }}
                 transition={{
                   height: { duration: 0.5 },
                   opacity: { duration: 2, repeat: Infinity, ease: "linear" }
                 }}
                 className={`w-full rounded-t-lg transition-all shadow-[0_0_20px_rgba(240,90,40,0.1)] ${
                   i === items.length - 1 ? "bg-primary shadow-[0_0_15px_rgba(240,90,40,0.4)]" : "bg-primary/30 group-hover:bg-primary/50"
                 }`}
               />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ActionBarChart;
