import { motion, AnimatePresence } from "framer-motion";
import { Monitor, Download, Key, Wifi, WifiOff, ArrowRight, Check, X, Loader2, RefreshCw } from "lucide-react";
import { useState, useEffect } from "react";
import { toast } from "sonner";

type ConnectionState = "no_sas" | "sas_offline" | "connected";

interface Props {
  connectionState: ConnectionState;
  onDismiss: () => void;
}

/**
 * Smart banner that detects 3 states:
 * 1. no_sas     → User never installed the SAS → "Download it"
 * 2. sas_offline → User has SAS but it's not running → "Open it"
 * 3. connected  → All good → Banner hidden
 */
const OnboardingBanner = ({ connectionState, onDismiss }: Props) => {
  const [dismissed, setDismissed] = useState(false);

  // Auto-dismiss when connected
  useEffect(() => {
    if (connectionState === "connected") {
      setDismissed(true);
    }
  }, [connectionState]);

  if (dismissed || connectionState === "connected") return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="w-full"
    >
      {connectionState === "no_sas" ? (
        /* STATE 1: Never installed */
        <div className="bg-gradient-to-r from-primary/[0.08] to-transparent border border-primary/20 rounded-2xl p-6 relative overflow-hidden">
          {/* Decorative glow */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl" />
          
          <div className="relative flex flex-col md:flex-row md:items-center gap-5">
            <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
              <Monitor className="w-6 h-6 text-primary" />
            </div>
            
            <div className="flex-1">
              <h3 className="font-display text-sm font-black text-foreground mb-1">
                Instale o WarmAds SAS no seu computador
              </h3>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                O WarmAds precisa do <span className="text-primary font-bold">SAS</span> rodando no PC onde o AdsPower está instalado. 
                Baixe, abra e ele conecta automaticamente.
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <a
                href="#"
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground font-display font-black text-[9px] uppercase tracking-[0.15em] shadow-[0_0_20px_rgba(240,90,40,0.25)] hover:shadow-[0_0_30px_rgba(240,90,40,0.4)] hover:-translate-y-0.5 transition-all"
              >
                <Download className="w-3.5 h-3.5" />
                BAIXAR SAS
              </a>
              <button
                onClick={onDismiss}
                className="p-2 rounded-lg hover:bg-white/5 text-muted-foreground/50 transition-all"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Quick steps */}
          <div className="relative mt-5 flex items-center gap-6 pt-4 border-t border-white/[0.04]">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center">
                <span className="text-[7px] font-black text-primary">1</span>
              </div>
              <span className="text-[9px] text-muted-foreground font-bold">Baixe o SAS</span>
            </div>
            <ArrowRight className="w-3 h-3 text-white/10" />
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                <span className="text-[7px] font-black text-white/30">2</span>
              </div>
              <span className="text-[9px] text-muted-foreground/50">Abra no PC</span>
            </div>
            <ArrowRight className="w-3 h-3 text-white/10" />
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                <span className="text-[7px] font-black text-white/30">3</span>
              </div>
              <span className="text-[9px] text-muted-foreground/50">Controle tudo daqui</span>
            </div>
          </div>
        </div>
      ) : (
        /* STATE 2: SAS installed but offline */
        <div className="bg-amber-500/[0.04] border border-amber-500/20 rounded-2xl p-5 relative">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
              <WifiOff className="w-5 h-5 text-amber-500" />
            </div>
            
            <div className="flex-1">
              <h3 className="font-display text-xs font-black text-foreground mb-0.5">
                SAS não detectado. Abra o WarmAds SAS no seu computador.
              </h3>
              <p className="text-[10px] text-muted-foreground">
                O app precisa estar aberto no PC para receber comandos do site.
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <Loader2 className="w-3 h-3 text-amber-500 animate-spin" />
                <span className="text-[8px] font-black text-amber-500 uppercase tracking-widest">
                  Aguardando SAS...
                </span>
              </div>
              <button
                onClick={onDismiss}
                className="p-2 rounded-lg hover:bg-white/5 text-muted-foreground/50 transition-all"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default OnboardingBanner;
