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
    { label: "PERFIS", active: false },
    { label: "ESTRATÉGIA", active: false },
    { label: "LOGS", active: false },
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
        <div className="flex items-center gap-2 bg-card border border-border rounded-full px-4 py-2 focus-within:border-primary/50 transition-colors">
          <input 
             type="password" 
             value={apiKey} 
             onChange={(e) => onApiKeyChange(e.target.value)}
             placeholder="Machine ID..."
             className="bg-transparent border-none outline-none text-[10px] font-mono text-muted-foreground w-24 placeholder:text-muted-foreground/30 focus:text-foreground transition-all focus:w-48"
          />
           <div className={`w-2 h-2 rounded-full ${isAgentConnected ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" : "bg-destructive/50"}`} title={isAgentConnected ? "Agent Online" : "Agent Offline"} />
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
