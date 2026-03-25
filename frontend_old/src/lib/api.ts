import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

export const checkHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const fetchProfiles = async () => {
  const res = await api.get('/profiles');
  return res.data.profiles;
};

export const startWarmup = async (profile_ids: string[], mode: string) => {
  const res = await api.post('/warmup/start', { profile_ids, mode });
  return res.data;
};

export const stopWarmup = async () => {
  const res = await api.post('/warmup/stop');
  return res.data;
};

export const fetchStatus = async () => {
  const res = await api.get('/warmup/status');
  return res.data;
};
