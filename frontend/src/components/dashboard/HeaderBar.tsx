import { Bell, LogOut, User, X, Lock, Eye, EyeOff, Minus, Square, Copy } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

interface HeaderBarProps {
  isActive: boolean;
  isAgentConnected?: boolean;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
}

const isElectron = typeof window !== 'undefined' && window.process && (window.process as any).type === 'renderer';
const ipc = isElectron ? (window as any).require('electron').ipcRenderer : null;

const HeaderBar = ({ isActive, isAgentConnected = false, apiKey, onApiKeyChange }: HeaderBarProps) => {
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
      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="flex items-center justify-between w-full py-6 border-b border-white/5 bg-background/50 backdrop-blur-md sticky top-0 z-40 px-6 lg:px-8 select-none relative"
        style={{ WebkitAppRegion: 'drag' } as any}
      >
        <div className="flex items-center gap-8" style={{ WebkitAppRegion: 'no-drag' } as any}>
          <div className="flex items-center gap-2 group cursor-pointer" onClick={() => navigate("/")}>
            <h1 className="font-display text-sm font-black text-foreground tracking-tight">
              WarmAds <span className="text-primary italic">Panel</span>
            </h1>
          </div>

        <div className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
             <button 
               key={link.label} 
               onClick={() => navigate(link.path)}
               className={`text-[9px] font-bold tracking-[0.15em] uppercase transition-all hover:text-primary ${currentPath === link.path ? "text-primary shadow-[0_2px_0_0_#FF4500]" : "text-muted-foreground"}`}
             >
               {link.label}
             </button>
          ))}
        </div>
        </div>

        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" style={{ WebkitAppRegion: 'no-drag' } as any}>
           <img src="/logo2.png" alt="WarmAds" className="h-20 w-auto opacity-100 transition-opacity drop-shadow-[0_0_15px_rgba(255,69,0,0.3)]" />
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
             <div className="flex items-center gap-2">
                <div className="w-1 h-1 rounded-full bg-primary animate-pulse shadow-[0_0_10px_#FF4500]" />
                <span className="text-[9px] font-bold tracking-[0.1em] text-primary uppercase">MOTOR ONLINE</span>
             </div>
          </div>

          <div className="h-4 w-px bg-white/10" />

          <div className="flex items-center gap-4" style={{ WebkitAppRegion: 'no-drag' } as any}>
             <button onClick={() => setShowPasswordModal(true)} className="p-2 hover:bg-white/5 rounded-full transition-colors text-muted-foreground hover:text-primary">
                <User className="w-4 h-4" />
             </button>
             <button onClick={handleLogout} className="p-2 hover:bg-white/5 rounded-full transition-colors text-muted-foreground hover:text-destructive">
                <LogOut className="w-4 h-4" />
             </button>
          </div>

          {/* Window Controls (Electron Only) */}
          {isElectron && (
            <div className="flex items-center ml-4 gap-1" style={{ WebkitAppRegion: 'no-drag' } as any}>
              <button 
                onClick={() => ipc?.send('window-minimize')}
                className="p-2.5 text-muted-foreground hover:bg-white/5 hover:text-foreground transition-all rounded-md"
              >
                <Minus className="w-3.5 h-3.5" />
              </button>
              <button 
                onClick={() => ipc?.send('window-toggle-maximize')}
                className="p-2.5 text-muted-foreground hover:bg-white/5 hover:text-foreground transition-all rounded-md"
              >
                <Square className="w-3 h-3" />
              </button>
              <button 
                onClick={() => ipc?.send('window-close')}
                className="p-2.5 text-muted-foreground hover:bg-destructive hover:text-destructive-foreground transition-all rounded-md"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </motion.header>

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
                      className="w-full bg-background border border-border/50 rounded-xl pl-10 pr-10 py-3 text-sm text-foreground placeholder:text-muted-foreground/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
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
                      className="w-full bg-background border border-border/50 rounded-xl pl-10 pr-10 py-3 text-sm text-foreground placeholder:text-muted-foreground/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
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

