import { Bell, Settings, User, X, Lock, Eye, EyeOff } from "lucide-react";
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
    { label: "DASHBOARD", active: true },
  ];

  return (
    <>
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
            {/* Engrenagem = Logout */}
            <button 
              onClick={handleLogout}
              title="Sair da conta"
              className="p-2 hover:bg-card hover:text-destructive rounded-full transition-colors"
            >
              <Settings className="w-4 h-4" />
            </button>
            {/* Ícone de usuário = Alterar Senha */}
            <button
              onClick={() => setShowPasswordModal(true)}
              title="Alterar senha"
              className="w-8 h-8 rounded-full bg-border overflow-hidden border border-border/50 ml-2 hover:border-primary/50 transition-colors"
            >
              <User className="w-full h-full p-1.5 text-muted-foreground/50 bg-card hover:text-primary transition-colors" />
            </button>
          </div>
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

