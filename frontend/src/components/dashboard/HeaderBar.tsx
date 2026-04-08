import { Bell, Settings, User } from "lucide-react";
import { motion } from "framer-motion";

interface HeaderBarProps {
  isActive: boolean;
  isAgentConnected?: boolean;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
}

const HeaderBar = ({ isActive, isAgentConnected = false, apiKey, onApiKeyChange }: HeaderBarProps) => {

  const navLinks = [
    { label: "DASHBOARD", active: true },
  ];

  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex items-center justify-between w-full pb-8 pt-2"
    >
      <div className="flex bg-card/40 rounded-full border border-border/40 p-1.5 px-6 gap-8">
        {navLinks.map((link) => (
           <button key={link.label} className={`text-[10px] font-bold tracking-widest uppercase transition-colors ${link.active ? "text-primary" : "text-muted-foreground hover:text-foreground"}`}>
             {link.label}
           </button>
        ))}
      </div>

      <div className="flex items-center gap-4">
        {/* Connection status hidden in desktop, using a cleaner API input here */}
        <div className="flex items-center gap-3 bg-card/60 border border-border/60 rounded-full px-5 py-2.5 focus-within:border-primary/50 transition-all shadow-inner">
          <span className="text-[9px] font-black text-primary uppercase tracking-[0.2em] hidden sm:block">ID</span>
          <input 
             type="text" 
             value={apiKey} 
             onChange={(e) => onApiKeyChange(e.target.value.trim())}
             placeholder="Seu Machine ID..."
             className="bg-transparent border-none outline-none text-[10px] font-mono text-foreground w-40 sm:w-64 placeholder:text-muted-foreground/30 focus:text-primary transition-all"
          />
          <div className="flex items-center gap-2 border-l border-border/40 pl-3">
             <div className={`w-2 h-2 rounded-full ${isAgentConnected ? "bg-emerald-500 animate-pulse shadow-[0_0_15px_rgba(16,185,129,0.8)]" : "bg-destructive/30"}`} title={isAgentConnected ? "Agente Online" : "Agente Offline"} />
             <span className={`text-[8px] font-bold uppercase tracking-widest ${isAgentConnected ? "text-emerald-500" : "text-muted-foreground"}`}>
               {isAgentConnected ? "Online" : "Offline"}
             </span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-muted-foreground">
          <button className="p-2 hover:bg-card rounded-full transition-colors"><Bell className="w-4 h-4" /></button>
          <button className="p-2 hover:bg-card rounded-full transition-colors"><Settings className="w-4 h-4" /></button>
          <div className="w-8 h-8 rounded-full bg-border overflow-hidden border border-border/50 ml-2">
            <User className="w-full h-full p-1.5 text-muted-foreground/50 bg-card" />
          </div>
        </div>
      </div>
    </motion.header>
  );
};

export default HeaderBar;
