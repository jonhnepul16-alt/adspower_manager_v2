import { Bell, LogOut, User, X, Lock, Eye, EyeOff, Minus, Square, Copy, Target, Download } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { GITHUB_DOWNLOAD_URL } from "@/lib/constants";

interface HeaderBarProps {
  isActive: boolean;
  isAgentConnected?: boolean;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  userEmail?: string;
  plan?: string;
}

// Robust Electron detection
const isElectron = typeof window !== 'undefined' && 
  (window.process?.versions?.electron || window.navigator.userAgent.toLowerCase().includes('electron'));
const ipc = isElectron ? (window as any).require('electron').ipcRenderer : null;

const HeaderBar = ({ isActive, isAgentConnected = false, apiKey, onApiKeyChange, userEmail, plan }: HeaderBarProps) => {
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate("/login");
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      toast.error("A senha deve ter pelo menos 6 caracteres.");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("As senhas não coincidem!");
      return;
    }
    setLoading(true);
    const { error } = await supabase.auth.updateUser({ password: newPassword });
    setLoading(false);
    if (error) {
      toast.error("Erro ao alterar senha: " + error.message);
    } else {
      toast.success("Senha alterada com sucesso!");
      setShowPasswordModal(false);
      setNewPassword("");
      setConfirmPassword("");
    }
  };

  const navLinks = [
    { label: "DASHBOARD", path: "/" },
    { label: "PERFIS", path: "/profiles" },
    { label: "AGENDAMENTO", path: "/scheduler" },
  ];

  const currentPath = window.location.pathname;

  return (
    <>

      <header className="flex flex-col w-full sticky top-0 z-40">
        <motion.div 
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex h-20 items-center justify-between px-6 lg:px-8 bg-background/80 backdrop-blur-xl border-b border-white/[0.05]"
          style={{ WebkitAppRegion: 'drag' } as any}
        >
          <div className="flex items-center gap-8" style={{ WebkitAppRegion: 'no-drag' } as any}>
            <div className="flex items-center gap-3 group cursor-pointer min-w-fit" onClick={() => navigate("/")}>
              <div className="w-14 h-14 flex items-center justify-center transition-all duration-300 transform group-hover:scale-105">
                <img src="logo2.png" alt="WarmAds" className="w-12 h-12 object-contain" />
              </div>
              <h1 className="font-display text-xl font-black text-white tracking-tight flex items-center gap-2 whitespace-nowrap">
                WarmAds <span className="bg-gradient-to-r from-orange-500 to-red-600 bg-clip-text text-transparent italic pr-1">Panel</span>
              </h1>
            </div>

            <nav className="hidden md:flex items-center gap-6 ml-4">
              {navLinks.map((link) => (
                <button 
                  key={link.label} 
                  onClick={() => navigate(link.path)}
                  className={`text-[9px] font-bold tracking-[0.15em] uppercase transition-all hover:text-primary relative py-2 ${
                    currentPath === link.path ? "text-primary" : "text-muted-foreground"
                  }`}
                >
                  {link.label}
                  {currentPath === link.path && (
                    <motion.div layoutId="nav-glow" className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary shadow-[0_0_10px_#FF4500] rounded-full" />
                  )}
                </button>
              ))}

              {!isElectron && (
                <a 
                  href={GITHUB_DOWNLOAD_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 transition-all group ml-2"
                >
                  <Download className="w-3 h-3 group-hover:-translate-y-0.5 transition-transform" />
                  <span className="text-[8px] font-black uppercase tracking-widest">BAIXAR APP</span>
                </a>
              )}
            </nav>
          </div>

          <div className="flex items-center gap-6" style={{ WebkitAppRegion: 'no-drag' } as any}>
            <div className="flex items-center gap-4">
              {plan && (
                <div className={`px-2.5 py-1 rounded-full text-[8px] font-black uppercase tracking-[0.15em] border transition-all ${
                  plan === "SCALE" 
                    ? "bg-primary/10 border-primary/30 text-primary shadow-[0_0_15px_rgba(255,69,0,0.1)]" 
                    : "bg-white/5 border-white/10 text-white/40"
                }`}>
                  {plan}
                </div>
              )}
              
              <div className="hidden lg:flex flex-col items-end mr-2">
                <span className="text-[8px] font-black text-white/20 uppercase tracking-widest">{userEmail}</span>
              </div>

              <div className="h-4 w-px bg-white/10 mx-2" />

              <div className="flex items-center gap-2">
                <button onClick={() => setShowPasswordModal(true)} className="p-2 hover:bg-white/5 rounded-full transition-colors text-muted-foreground hover:text-primary">
                  <User className="w-4 h-4" />
                </button>
                <button onClick={handleLogout} className="p-2 hover:bg-white/5 rounded-full transition-colors text-muted-foreground hover:text-destructive">
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>

            {isElectron && (
              <div className="flex items-center gap-1 border-l border-white/10 pl-4">
                <button onClick={() => ipc?.send('window-minimize')} className="p-2 text-muted-foreground hover:text-white transition-colors"><Minus className="w-3.5 h-3.5" /></button>
                <button onClick={() => ipc?.send('window-toggle-maximize')} className="p-2 text-muted-foreground hover:text-white transition-colors"><Square className="w-3 h-3" /></button>
                <button onClick={() => ipc?.send('window-close')} className="p-2 text-muted-foreground hover:text-destructive transition-colors"><X className="w-3.5 h-3.5" /></button>
              </div>
            )}
          </div>
        </motion.div>
      </header>

      {/* Modal de Alterar Senha */}
      <AnimatePresence>
        {showPasswordModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
            onClick={() => setShowPasswordModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className="bg-card border border-border/50 rounded-2xl p-8 w-full max-w-md mx-4 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="font-display text-lg font-black text-foreground">Alterar Senha</h2>
                  <p className="text-xs text-muted-foreground mt-0.5">Defina uma nova senha de acesso</p>
                </div>
                <button onClick={() => setShowPasswordModal(false)} className="p-2 rounded-full hover:bg-border/50 text-muted-foreground transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleChangePassword} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Nova Senha</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <input
                      type={showNew ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full bg-background border border-border/50 rounded-xl pl-10 pr-10 py-3 text-sm text-foreground placeholder:text-muted-foreground/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all font-mono"
                      placeholder="Mínimo 6 caracteres"
                      required
                    />
                    <button type="button" onClick={() => setShowNew(!showNew)} className="absolute inset-y-0 right-0 pr-3 flex items-center text-muted-foreground hover:text-foreground transition-colors">
                      {showNew ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Confirmar Senha</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <input
                      type={showConfirm ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full bg-background border border-border/50 rounded-xl pl-10 pr-10 py-3 text-sm text-foreground placeholder:text-muted-foreground/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all font-mono"
                      placeholder="Repita a nova senha"
                      required
                    />
                    <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute inset-y-0 right-0 pr-3 flex items-center text-muted-foreground hover:text-foreground transition-colors">
                      {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 flex items-center justify-center gap-2 px-6 py-3.5 rounded-full font-display font-bold text-xs uppercase tracking-[0.2em] bg-primary text-primary-foreground hover:-translate-y-0.5 transition-all disabled:opacity-60 disabled:cursor-wait shadow-[0_0_20px_-5px_rgba(240,90,40,0.4)] hover:shadow-[0_0_30px_0px_rgba(240,90,40,0.6)]"
                >
                  {loading ? "Salvando..." : "Salvar Nova Senha"}
                </button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default HeaderBar;
