import { useState, useEffect } from "react";
import { Plus, Trash2, Edit2, Tag as TagIcon, Search, Users, ArrowLeft, Save, X, Clock } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import GlassCard from "@/components/dashboard/GlassCard";
import HeaderBar from "@/components/dashboard/HeaderBar";
import { toast } from "sonner";
import { fetchProfiles, createProfile, updateProfile, deleteProfile, fetchStatus } from "@/lib/api";
import { supabase } from "@/lib/supabase";

interface Profile {
  id: string;
  name: string;
  adsPowerId?: string; // mapping to DB id implicitly or explicitly
  tag: string;
  history?: { date: string, duration: number }[];
}

const Profiles = () => {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [activeProfile, setActiveProfile] = useState<Profile | null>(null);
  const [editingProfile, setEditingProfile] = useState<Profile | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [userEmail, setUserEmail] = useState<string>("");
  const [plan, setPlan] = useState<string>("START");
  const navigate = useNavigate();

  // Form State
  const [name, setName] = useState("");
  const [adsId, setAdsId] = useState("");
  const [tag, setTag] = useState("");

  const loadProfiles = async () => {
    try {
      const dbProfiles = await fetchProfiles();
      const mappedProfiles = (dbProfiles || []).map((p: any) => ({
        id: p.id,
        adsPowerId: p.id,
        name: p.name,
        tag: p.tag,
        history: p.history || []
      }));
      setProfiles(mappedProfiles);
      return mappedProfiles;
    } catch (e) {
      console.error("Failed to load profiles from backend", e);
      return [];
    }
  };

  useEffect(() => {
    const init = async () => {
      // Fetch user email
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user?.email) {
        setUserEmail(session.user.email);
      }

      // Fetch plan status
      try {
        const machineId = localStorage.getItem("vexel_machine_id") || "local_agent";
        const status = await fetchStatus(machineId);
        if (status?.plan_status?.plan) {
          setPlan(status.plan_status.plan);
        }
      } catch (e) {
        console.error("Failed to fetch plan status", e);
      }

      const dbProfiles = await loadProfiles();
      // Migration from localStorage
      const saved = localStorage.getItem("warmads_profiles");
      if (saved) {
        try {
          const localProfiles = JSON.parse(saved);
          if (localProfiles.length > 0 && dbProfiles.length === 0) {
            toast.info("Sincronizando perfis locais com o servidor...");
            for (const p of localProfiles) {
               try {
                 await createProfile({ id: p.adsPowerId || p.id, name: p.name, tag: p.tag || "Geral" });
               } catch (ex) {
                 console.log("Migration skip: ", p.name);
               }
            }
            await loadProfiles();
            // Limpa após migrar
            localStorage.removeItem("warmads_profiles");
          }
        } catch (e) {
             console.error("Migration parse error", e);
        }
      }
    };
    init();
  }, []);

  const handleAddOrEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !adsId) {
      toast.error("Nome e ID são obrigatórios!");
      return;
    }

    try {
      if (editingProfile) {
        await updateProfile(editingProfile.adsPowerId || editingProfile.id, { id: adsId, name, tag });
        toast.success("Perfil atualizado com sucesso!");
      } else {
        await createProfile({ id: adsId, name, tag: tag || "Geral" });
        toast.success("Perfil adicionado com sucesso!");
      }
      await loadProfiles();
      closeModal();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao salvar perfil");
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm("Tem certeza que deseja excluir este perfil?")) {
      try {
        await deleteProfile(id);
        toast.success("Perfil excluído.");
        await loadProfiles();
      } catch (err) {
        toast.error("Erro ao excluir perfil");
      }
    }
  };

  const openModal = (profile?: Profile) => {
    if (profile) {
      setEditingProfile(profile);
      setName(profile.name);
      setAdsId(profile.adsPowerId);
      setTag(profile.tag);
    } else {
      setEditingProfile(null);
      setName("");
      setAdsId("");
      setTag("");
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingProfile(null);
  };

  const openHistoryModal = (profile: Profile) => {
    setActiveProfile(profile);
    setIsHistoryModalOpen(true);
  };

  const closeHistoryModal = () => {
    setIsHistoryModalOpen(false);
    setActiveProfile(null);
  };

  const filteredProfiles = profiles.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.tag?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.adsPowerId?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background text-foreground font-body">
      <HeaderBar 
        isActive={false} 
        apiKey={localStorage.getItem("vexel_machine_id") || "local_agent"} 
        onApiKeyChange={(val) => localStorage.setItem("vexel_machine_id", val)} 
        userEmail={userEmail}
        plan={plan}
      />

      <main className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-5 h-5 text-primary" />
              <h1 className="font-display text-2xl font-black text-foreground tracking-tight uppercase">Gerenciar Perfis</h1>
            </div>
            <p className="text-sm text-muted-foreground">Cadastre seus perfis do AdsPower para acesso rápido no dashboard.</p>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/50" />
              <input 
                type="text" 
                placeholder="Buscar por nome ou tag..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-white/[0.03] border border-white/[0.05] rounded-full pl-10 pr-6 py-2.5 text-xs focus:outline-none focus:border-primary/50 transition-all w-full md:w-64"
              />
            </div>
            <button 
              onClick={() => openModal()}
              className="flex items-center gap-2 px-6 py-2.5 rounded-full bg-primary text-primary-foreground font-display font-bold text-[10px] uppercase tracking-widest shadow-[0_0_20px_rgba(240,90,40,0.3)] hover:shadow-[0_0_30px_rgba(240,90,40,0.5)] transition-all hover:-translate-y-0.5"
            >
              <Plus className="w-4 h-4" />
              NOVO PERFIL
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <AnimatePresence mode="popLayout">
            {filteredProfiles.map((profile, i) => (
              <motion.div
                key={profile.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: i * 0.05 }}
              >
                <GlassCard className="p-6 h-full flex flex-col group hover:border-primary/20 transition-all">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-2.5 bg-primary/10 rounded-xl">
                      <Users className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button 
                        onClick={() => openModal(profile)}
                        className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground hover:text-foreground transition-colors"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button 
                        onClick={() => handleDelete(profile.id)}
                        className="p-2 hover:bg-destructive/10 rounded-lg text-muted-foreground hover:text-destructive transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <h3 className="font-display font-bold text-lg mb-1 truncate">{profile.name}</h3>
                  <code className="text-[10px] text-muted-foreground font-mono bg-white/[0.03] px-2 py-1 rounded-md mb-4 inline-block w-fit">
                    ID: {profile.adsPowerId}
                  </code>

                  <div className="mt-auto flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 px-3 py-1 bg-white/[0.03] border border-white/[0.05] rounded-full">
                      <TagIcon className="w-3 h-3 text-primary/50" />
                      <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-tight">{profile.tag}</span>
                    </div>
                    
                    <button 
                       onClick={() => openHistoryModal(profile)}
                       className="text-[10px] font-bold text-primary opacity-50 hover:opacity-100 transition-opacity uppercase tracking-widest flex items-center gap-1"
                    >
                       Histórico
                       <span className="bg-primary/20 text-primary px-1.5 py-0.5 rounded-md text-[8px]">{profile.history?.length || 0}</span>
                    </button>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </AnimatePresence>

          {filteredProfiles.length === 0 && (
            <div className="col-span-full py-20 flex flex-col items-center justify-center text-center opacity-30">
              <Users className="w-16 h-16 mb-4" />
              <p className="font-display font-bold uppercase tracking-widest text-sm">Nenhum perfil encontrado</p>
              <button onClick={() => openModal()} className="mt-4 text-primary text-xs font-bold hover:underline">Adicionar primeiro perfil</button>
            </div>
          )}
        </div>
      </main>

      {/* Modal Add/Edit */}
      <AnimatePresence>
        {isModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={closeModal}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-card border border-border/50 rounded-2xl p-8 w-full max-w-md shadow-2xl overflow-hidden relative"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/50 to-primary" />
              
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h2 className="font-display text-xl font-black text-foreground uppercase tracking-tight">
                    {editingProfile ? "Editar Perfil" : "Novo Perfil"}
                  </h2>
                  <p className="text-xs text-muted-foreground mt-1">Insira os detalhes do perfil AdsPower</p>
                </div>
                <button onClick={closeModal} className="p-2 hover:bg-white/5 rounded-full text-muted-foreground transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleAddOrEdit} className="space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Nome do Perfil</label>
                  <input 
                    autoFocus
                    type="text" 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ex: Facebook Principal 01"
                    className="w-full bg-white/[0.02] border border-white/[0.05] rounded-xl p-4 text-sm focus:outline-none focus:border-primary/50 transition-all font-display font-medium"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">AdsPower ID</label>
                  <input 
                    type="text" 
                    value={adsId}
                    onChange={(e) => setAdsId(e.target.value)}
                    placeholder="Ex: k1aq7vt0"
                    className="w-full bg-white/[0.02] border border-white/[0.05] rounded-xl p-4 text-sm focus:outline-none focus:border-primary/50 transition-all font-mono"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Tag / Categoria</label>
                  <input 
                    type="text" 
                    value={tag}
                    onChange={(e) => setTag(e.target.value)}
                    placeholder="Ex: Aquecimento, Contingência..."
                    className="w-full bg-white/[0.02] border border-white/[0.05] rounded-xl p-4 text-sm focus:outline-none focus:border-primary/50 transition-all"
                  />
                </div>

                <div className="pt-4 flex gap-4">
                  <button 
                    type="button"
                    onClick={closeModal}
                    className="flex-1 py-4 rounded-full border border-white/5 font-display font-bold text-[10px] uppercase tracking-widest hover:bg-white/5 transition-all text-muted-foreground"
                  >
                    CANCELAR
                  </button>
                  <button 
                    type="submit"
                    className="flex-1 py-4 rounded-full bg-primary text-primary-foreground font-display font-bold text-[10px] uppercase tracking-widest shadow-[0_0_20px_rgba(240,90,40,0.3)] hover:shadow-[0_0_30px_rgba(240,90,40,0.5)] transition-all hover:-translate-y-0.5"
                  >
                    {editingProfile ? "SALVAR ALTERAÇÕES" : "CRIAR PERFIL"}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Modal Histórico */}
      <AnimatePresence>
        {isHistoryModalOpen && activeProfile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={closeHistoryModal}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-card border border-border/50 rounded-2xl p-8 w-full max-w-md shadow-2xl overflow-hidden relative flex flex-col max-h-[80vh]"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/50 to-primary" />
              
              <div className="flex items-center justify-between mb-6 shrink-0">
                <div>
                  <h2 className="font-display text-xl font-black text-foreground uppercase tracking-tight">
                    Histórico do Perfil
                  </h2>
                  <p className="text-xs text-primary font-bold mt-1 max-w-[250px] truncate">{activeProfile.name}</p>
                </div>
                <button onClick={closeHistoryModal} className="p-2 hover:bg-white/5 rounded-full text-muted-foreground transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="overflow-y-auto pr-2 flex-1 space-y-3 hide-scrollbar">
                {(!activeProfile.history || activeProfile.history.length === 0) ? (
                   <div className="py-12 flex flex-col items-center justify-center text-center opacity-30">
                      <Clock className="w-8 h-8 mb-4" />
                      <p className="font-display font-bold uppercase tracking-widest text-xs">Nenhum aquecimento</p>
                   </div>
                ) : (
                   [...activeProfile.history].reverse().map((exec, idx) => (
                      <div key={idx} className="flex items-center justify-between bg-white/[0.02] border border-white/[0.05] p-3 rounded-xl">
                         <span className="text-xs text-muted-foreground font-mono">{exec.date}</span>
                         <span className="text-[10px] bg-primary/20 text-primary font-black uppercase tracking-widest px-3 py-1.5 rounded-full">
                           {exec.duration} minutos
                         </span>
                      </div>
                   ))
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Profiles;
