import { useState } from "react";
import { motion } from "framer-motion";
import { supabase } from "@/lib/supabase";
import { GITHUB_DOWNLOAD_URL } from "@/lib/constants";
import { Target, Shield, Settings, HelpCircle, LogOut, Download } from "lucide-react";
import { useNavigate } from "react-router-dom";

const Sidebar = () => {
  const [activeItem, setActiveItem] = useState("COMMAND");
  const navigate = useNavigate();

  // Robust Electron detection
  const isElectron = typeof window !== 'undefined' && 
    (window.process?.versions?.electron || window.navigator.userAgent.toLowerCase().includes('electron'));

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate("/login");
  };

  const menuItems = [
    { id: "COMMAND", label: "COMANDOS", icon: Target },
  ];

  return (
    <div className="w-64 h-screen bg-[#0F0F10] border-r border-border/10 flex flex-col pt-8 pb-6 px-4 sticky top-0">
      <div className="mb-12 px-4">
        <h1 className="font-display text-2xl font-black text-primary tracking-tight">
           Warm <span className="text-foreground">Ads</span>
        </h1>
      </div>

      <div className="mb-4 px-4">
        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1 opacity-60">CENTRAL DE COMANDO</p>
        <p className="text-sm font-semibold text-foreground">Sessão Ativa</p>
      </div>

      <nav className="flex-1 space-y-2 mt-4">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveItem(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 ${
              activeItem === item.id
                ? "bg-primary text-primary-foreground font-bold shadow-[0_0_20px_-5px_rgba(251,191,36,0.3)]"
                : "text-muted-foreground hover:bg-card hover:text-foreground font-medium"
            }`}
          >
            <item.icon className={`w-[18px] h-[18px] ${activeItem === item.id ? "text-primary-foreground" : "text-muted-foreground/70"}`} />
            <span className="text-xs uppercase tracking-widest">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="mt-auto space-y-2 pt-8 border-t border-border/10">
        {!isElectron && (
          <a 
            href={GITHUB_DOWNLOAD_URL}
            className="w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 transition-all duration-300 mb-2 group"
          >
            <Download className="w-[18px] h-[18px] group-hover:-translate-y-0.5 transition-transform" />
            <span className="text-[10px] uppercase tracking-widest font-black">BAIXAR APP</span>
          </a>
        )}
        <button className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-muted-foreground hover:bg-card hover:text-foreground transition-all duration-300">
          <HelpCircle className="w-[18px] h-[18px] text-muted-foreground/70" />
          <span className="text-xs uppercase tracking-widest font-medium">AJUDA</span>
        </button>
        <button 
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-muted-foreground hover:bg-card hover:text-foreground hover:text-destructive transition-all duration-300"
        >
          <LogOut className="w-[18px] h-[18px] text-muted-foreground/70" />
          <span className="text-xs uppercase tracking-widest font-medium">SAIR</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
