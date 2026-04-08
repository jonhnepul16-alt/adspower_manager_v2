import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabase";
import { toast } from "sonner";
import { Zap, Lock, Mail } from "lucide-react";
import { motion } from "framer-motion";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        toast.error("Erro ao fazer login: " + error.message);
      } else {
        toast.success("Login realizado com sucesso!");
        navigate("/");
      }
    } catch (err: any) {
      toast.error("Ocorreu um erro no login.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 z-0 opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/30 blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-primary/20 blur-[100px]"></div>
      </div>

      <div className="z-10 w-full max-w-md p-6">
        <div className="flex flex-col items-center mb-8">
          <div className="w-48 h-20 mb-4 flex items-center justify-center relative">
            <img src="/logo2.png" alt="Warm Ads" className="absolute w-full h-full object-contain" />
          </div>
          <h1 className="font-display text-2xl font-black text-foreground tracking-tight text-center">
            Acesso Restrito
          </h1>
          <p className="text-sm text-foreground/50 mt-1">
            Painel de automação de elite
          </p>
        </div>

        <motion.div
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ duration: 0.5 }}
           className="glass p-8"
         >
          <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider pl-1">
                E-mail
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-card border border-border/50 rounded-xl pl-10 pr-4 py-3 text-sm font-body text-foreground placeholder:text-muted-foreground/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
                  placeholder="Seu e-mail de acesso"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider pl-1">
                Senha
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-4 w-4 text-muted-foreground" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-card border border-border/50 rounded-xl pl-10 pr-4 py-3 text-sm font-body text-foreground placeholder:text-muted-foreground/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
                  placeholder="Sua senha secreta"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`w-full flex items-center justify-center gap-2 px-6 py-3.5 mt-4 rounded-full font-display font-bold text-xs uppercase tracking-[0.2em] transition-all
                  ${loading 
                    ? 'opacity-70 cursor-wait bg-muted text-muted-foreground' 
                    : "bg-primary text-primary-foreground shadow-[0_0_20px_-5px_rgba(251,191,36,0.4)] hover:shadow-[0_0_30px_0px_rgba(251,191,36,0.6)] hover:-translate-y-0.5"
                  }
              `}
            >
              {loading ? "Autenticando..." : "Entrar no Sistema"}
              {!loading && <Zap className="w-4 h-4 ml-1" />}
            </button>
          </form>
        </motion.div>
      </div>
    </div>
  );
};

export default Login;
