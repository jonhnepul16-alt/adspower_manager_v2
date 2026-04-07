import { useState, useEffect } from "react";
import { Clock, Key, Trash2, Plus, CalendarDays } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Rule {
  id: string;
  name: string;
  start: string;
  end: string;
  enabled: boolean;
  type: "time" | "weekend";
}

interface Props {
  config: any;
  status: any;
  onUpdate: (config: any) => void;
}

const SchedulerConfig = ({ config, status, onUpdate }: Props) => {
  // Sync the external config if needed, otherwise use local state to handle rules
  const [rules, setRules] = useState<Rule[]>(() => {
     if (config && config.rules && Array.isArray(config.rules)) {
        return config.rules;
     }
     return [
        { id: "1", name: "Horário Comercial", start: "09:00", end: "18:00", enabled: true, type: "time" },
        { id: "2", name: "Final de Semana", start: "10:00", end: "14:00", enabled: false, type: "weekend" }
     ];
  });
  
  const [isAdding, setIsAdding] = useState(false);
  const [newRule, setNewRule] = useState<Partial<Rule>>({ name: "", start: "00:00", end: "23:59", type: "time" });

  useEffect(() => {
     if (config && config.rules && Array.isArray(config.rules)) {
        setRules(config.rules);
     }
  }, [config]);

  if (!config) return <div className="text-muted-foreground text-xs animate-pulse">Carregando Módulos...</div>;

  const pushUpdate = (newRules: Rule[]) => {
    setRules(newRules);
    
    // Convert rules array to 'windows' dictionary to perfectly match the Python agent's (gui_agent.py) expected format
    const windowsObj: Record<string, any> = {};
    newRules.forEach((rule, index) => {
       windowsObj[rule.id || String(index)] = {
          enabled: rule.enabled,
          start: rule.start,
          end: rule.end
       };
    });

    onUpdate({ ...config, rules: newRules, windows: windowsObj });
  };

  const handleToggleRule = (id: string) => {
    const newRules = rules.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r);
    pushUpdate(newRules);
  };

  const handleDeleteRule = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newRules = rules.filter(r => r.id !== id);
    pushUpdate(newRules);
  };

  const handleSaveAdd = () => {
     if (!newRule.name) return;
     const newRules = [...rules, { ...newRule, id: Date.now().toString(), enabled: true } as Rule];
     pushUpdate(newRules);
     setIsAdding(false);
     setNewRule({ name: "", start: "00:00", end: "23:59", type: "time" });
  };

  return (
    <div className="flex flex-col gap-4">
       
       <AnimatePresence>
         {rules.map((rule) => (
           <motion.div 
              key={rule.id}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, height: 0, marginBottom: 0 }}
              className={`relative p-4 rounded-2xl border transition-all duration-300 flex items-center justify-between group ${rule.enabled ? 'bg-card border-border shadow-lg' : 'bg-background/50 border-transparent hover:bg-card/50'}`}
           >
              <div className="flex items-center gap-4">
                 <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${rule.enabled ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'}`}>
                    {rule.type === 'weekend' ? <Key className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                 </div>
                 <div>
                    <h4 className={`text-[11px] font-bold ${rule.enabled ? 'text-foreground' : 'text-foreground/70'}`}>{rule.name}</h4>
                    <p className="text-[10px] text-muted-foreground/60 leading-tight">
                       {rule.type === 'weekend' ? 'Frequência reduzida' : `${rule.start} - ${rule.end}`}<br/>{rule.type === 'weekend' ? '' : '(BRT)'}
                    </p>
                 </div>
              </div>

              <div className="flex items-center gap-3">
                 <button 
                   onClick={(e) => handleDeleteRule(rule.id, e)}
                   className="opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-destructive/10 rounded-full text-destructive/60 hover:text-destructive"
                 >
                    <Trash2 className="w-4 h-4" />
                 </button>
                 
                 <button 
                    onClick={() => handleToggleRule(rule.id)}
                    className={`w-12 h-6 rounded-full transition-colors relative flex items-center px-1 ${rule.enabled ? 'bg-emerald-500' : 'bg-muted-foreground/30'}`}
                 >
                    <motion.div 
                      animate={{ x: rule.enabled ? 24 : 0 }}
                      className="w-4 h-4 bg-white rounded-full shadow-sm"
                    />
                 </button>
              </div>
           </motion.div>
         ))}
       </AnimatePresence>

       {isAdding ? (
         <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="p-4 rounded-2xl border border-primary/40 bg-card shadow-[0_0_20px_-5px_rgba(251,191,36,0.1)] flex flex-col gap-3"
         >
            <input 
              type="text" 
              placeholder="Nome da Regra (ex: Madrugada)"
              className="w-full bg-background/50 border border-border/50 rounded-lg px-3 py-2 text-xs font-medium text-foreground outline-none focus:border-primary/50 placeholder:text-muted-foreground/50 text-[10px]"
              value={newRule.name}
              onChange={e => setNewRule({...newRule, name: e.target.value})}
            />
            <div className="flex gap-2">
               <input 
                 type="time" 
                 className="flex-1 bg-background/50 border border-border/50 rounded-lg px-3 py-2 text-xs text-foreground outline-none focus:border-primary/50 text-[10px]"
                 value={newRule.start}
                 onChange={e => setNewRule({...newRule, start: e.target.value})}
               />
               <input 
                 type="time" 
                 className="flex-1 bg-background/50 border border-border/50 rounded-lg px-3 py-2 text-xs text-foreground outline-none focus:border-primary/50 text-[10px]"
                 value={newRule.end}
                 onChange={e => setNewRule({...newRule, end: e.target.value})}
               />
            </div>
            <div className="flex gap-2 mt-2">
                <button 
                  onClick={() => setIsAdding(false)} 
                  className="flex-1 py-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest hover:text-foreground transition-colors"
                >
                  Cancelar
                </button>
                <button 
                  onClick={handleSaveAdd} 
                  className="flex-1 py-2 bg-primary text-primary-foreground text-[10px] font-bold uppercase tracking-widest rounded-lg shadow-sm hover:brightness-110 transition-all"
                >
                  Salvar
                </button>
            </div>
         </motion.div>
       ) : (
         <button 
            onClick={() => setIsAdding(true)}
            className="mt-2 w-full py-4 border border-border/50 rounded-2xl border-dashed text-xs font-bold text-muted-foreground tracking-widest uppercase hover:border-primary/50 hover:text-primary hover:bg-primary/5 transition-all flex items-center justify-center gap-2"
         >
            <span className="text-lg leading-none">+</span> ADICIONAR REGRA
         </button>
       )}
    </div>
  );
};

export default SchedulerConfig;
