import axios from 'axios';
import { supabase } from './supabase';

// Auto-detect: local SAS (Electron/localhost) uses /api proxy, cloud site uses Railway
const CLOUD_API = 'https://web-production-373eb.up.railway.app/api';

const isElectron = typeof window !== 'undefined' && window.process && (window.process as any).type === 'renderer';
const isLocalhost = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

let detectedApiUrl = CLOUD_API;
if (isElectron) {
  detectedApiUrl = 'http://localhost:8000/api'; // Direct to python backend in Electron (works in file:// and dev)
} else if (isLocalhost) {
  detectedApiUrl = '/api'; // Use vite proxy for normal browser dev
}

const API_BASE_URL = import.meta.env.VITE_API_URL || detectedApiUrl;

const api = axios.create({
  baseURL: API_BASE_URL, 
});

// Add a request interceptor to inject the Supabase access token
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});


export const checkHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const fetchProfiles = async () => {
  const res = await api.get('/profiles');
  return res.data.profiles;
};

export const createProfile = async (profileData: { id: string, name: string, tag: string }) => {
  const res = await api.post('/profiles', profileData);
  return res.data.profile;
};

export const updateProfile = async (id: string, profileData: { id: string, name: string, tag: string }) => {
  const res = await api.put(`/profiles/${id}`, profileData);
  return res.data.profile;
};

export const deleteProfile = async (id: string) => {
  const res = await api.delete(`/profiles/${id}`);
  return res.data;
};

export const startWarmup = async (profile_ids: string[], mode: string, duration?: number, machine_id: string = "default", minimized: boolean = false) => {
  const res = await api.post('/warmup/start', { profile_ids, mode, duration, machine_id, minimized });
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
