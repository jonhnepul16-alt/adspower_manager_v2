import axios from 'axios';

// Use internal environment variable or fallback to /api for proxy
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL, 
});


export const checkHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const fetchProfiles = async () => {
  const res = await api.get('/profiles');
  return res.data.profiles;
};

export const startWarmup = async (profile_ids: string[], mode: string, machine_id: string = "default") => {
  const res = await api.post('/warmup/start', { profile_ids, mode, machine_id });
  return res.data;
};

export const stopWarmup = async (machine_id: string = "default") => {
  const res = await api.post('/warmup/stop', null, { params: { machine_id } });
  return res.data;
};

export const fetchStatus = async (machine_id: string = "default") => {
  const res = await api.get('/warmup/status', { params: { machine_id } });
  return res.data;
};

export const updateScheduler = async (machine_id: string, config: any) => {
  const res = await api.post('/scheduler/update', config, { params: { machine_id } });
  return res.data;
};
