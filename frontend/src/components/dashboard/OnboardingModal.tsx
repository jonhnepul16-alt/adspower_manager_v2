import { motion, AnimatePresence } from "framer-motion";
import { Monitor, Download, Key, Wifi, WifiOff, ArrowRight, Check, X, Copy } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (machineId: string) => void;
  agentConnected: boolean;
}

const OnboardingModal = ({ isOpen, onClose, onConnect, agentConnected }: Props) => {
  const [step, setStep] = useState<"intro" | "connect">("intro");
  const [machineId, setMachineId] = useState("");

  const handleConnect = () => {
    const id = machineId.trim();
    if (!id) {
      toast.error("Cole o Machine ID do seu SAS");
      return;
    }
    onConnect(id);
    toast.success("Conectando ao SAS...");
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 30 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 30 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="bg-[#0a0a0a] border border-white/10 rounded-3xl w-full max-w-lg overflow-hidden shadow-[0_0_80px_rgba(240,90,40,0.1)]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header glow */}
            <div className="h-1 w-full bg-gradient-to-r from-transparent via-primary to-transparent" />

            <div className="p-8">
              {step === "intro" ? (
                <>
                  {/* Intro */}
                  <div className="flex items-center justify-between mb-6">
                    <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                      <Monitor className="w-7 h-7 text-primary" />
                    </div>
                    <button onClick={onClose} className="p-2 rounded-full hover:bg-white/5 text-muted-foreground">
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <h2 className="font-display text-xl font-black text-foreground mb-2">
                    Bem-vindo ao WarmAds! 🔥
                  </h2>
                  <p className="text-sm text-muted-foreground leading-relaxed mb-8">
                    Para aquecer perfis pelo site, você precisa do{" "}
                    <span className="text-primary font-bold">WarmAds SAS</span> rodando no
                    seu computador com o AdsPower.
                  </p>

                  {/* Steps */}
                  <div className="space-y-3 mb-8">
                    <div className="flex items-center gap-4 p-4 bg-white/[0.02] border border-white/[0.05] rounded-xl">
                      <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center shrink-0">
                        <span className="text-xs font-black text-primary">1</span>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-foreground">Baixe e abra o WarmAds SAS no seu PC</p>
                        <p className="text-[10px] text-muted-foreground">O app se conecta automaticamente ao AdsPower</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 p-4 bg-white/[0.02] border border-white/[0.05] rounded-xl">
                      <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center shrink-0">
                        <span className="text-xs font-black text-primary">2</span>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-foreground">Copie o <span className="text-primary">SAS ID</span> que aparece no rodapé</p>
                        <p className="text-[10px] text-muted-foreground">O ID é gerado automaticamente pelo seu computador</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 p-4 bg-white/[0.02] border border-white/[0.05] rounded-xl">
                      <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center shrink-0">
                        <span className="text-xs font-black text-primary">3</span>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-foreground">Cole o SAS ID aqui e controle tudo remotamente</p>
                        <p className="text-[10px] text-muted-foreground">Funciona do celular, tablet ou qualquer navegador</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <a
                      href="#"
                      className="flex-1 flex items-center justify-center gap-2 py-3.5 rounded-xl bg-primary text-primary-foreground font-display font-black text-[10px] uppercase tracking-[0.2em] shadow-[0_0_25px_rgba(240,90,40,0.3)] hover:shadow-[0_0_35px_rgba(240,90,40,0.5)] hover:-translate-y-0.5 transition-all"
                    >
                      <Download className="w-4 h-4" />
                      BAIXAR SAS
                    </a>
                    <button
                      onClick={() => setStep("connect")}
                      className="flex-1 flex items-center justify-center gap-2 py-3.5 rounded-xl bg-white/[0.03] border border-white/[0.08] text-foreground font-display font-black text-[10px] uppercase tracking-[0.2em] hover:bg-white/[0.06] transition-all"
                    >
                      <Key className="w-4 h-4" />
                      JÁ TENHO
                    </button>
                  </div>
                </>
              ) : (
                <>
                  {/* Connect with SAS ID */}
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setStep("intro")}
                        className="p-2 rounded-full hover:bg-white/5 text-muted-foreground"
                      >
                        <ArrowRight className="w-4 h-4 rotate-180" />
                      </button>
                      <h2 className="font-display text-lg font-black text-foreground">
                        Conectar ao SAS
                      </h2>
                    </div>
                    <button onClick={onClose} className="p-2 rounded-full hover:bg-white/5 text-muted-foreground">
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                    Abra o WarmAds SAS no seu PC. No rodapé do dashboard, você verá o{" "}
                    <span className="text-primary font-bold">SAS ID</span>. 
                    Copie e cole abaixo.
                  </p>

                  {/* SAS ID Input */}
                  <div className="mb-4">
                    <label className="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-2 block flex items-center gap-1.5">
                      <Key className="w-3 h-3" />
                      SAS ID (Machine ID)
                    </label>
                    <input
                      type="text"
                      value={machineId}
                      onChange={(e) => setMachineId(e.target.value)}
                      placeholder="Ex: a1b2c3d4e5f6..."
                      className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-3.5 text-sm font-mono text-foreground outline-none focus:border-primary/40 focus:shadow-[0_0_20px_rgba(240,90,40,0.1)] transition-all placeholder:text-white/10"
                      autoFocus
                    />
                    <p className="text-[8px] text-white/15 mt-1.5 italic">
                      Esse ID é gerado automaticamente pelo SAS e aparece no rodapé do app
                    </p>
                  </div>

                  {/* Status */}
                  <div className={`flex items-center gap-2 p-3 rounded-xl mb-6 ${
                    agentConnected 
                      ? "bg-emerald-500/[0.06] border border-emerald-500/20" 
                      : "bg-white/[0.02] border border-white/[0.05]"
                  }`}>
                    {agentConnected ? (
                      <>
                        <Wifi className="w-4 h-4 text-emerald-500" />
                        <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest">
                          SAS conectado e pronto!
                        </span>
                      </>
                    ) : (
                      <>
                        <WifiOff className="w-4 h-4 text-muted-foreground" />
                        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                          Certifique-se que o SAS está aberto no PC
                        </span>
                      </>
                    )}
                  </div>

                  <button
                    onClick={handleConnect}
                    disabled={!machineId.trim()}
                    className={`w-full py-3.5 rounded-xl font-display font-black text-[10px] uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-2
                      ${machineId.trim()
                        ? "bg-primary text-primary-foreground shadow-[0_0_25px_rgba(240,90,40,0.3)] hover:-translate-y-0.5"
                        : "bg-white/[0.03] border border-white/[0.06] text-white/20 cursor-not-allowed"
                      }
                    `}
                  >
                    <Check className="w-4 h-4" />
                    CONECTAR
                  </button>
                </>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default OnboardingModal;
