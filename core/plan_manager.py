import os
import json
import uuid
import datetime
import time
import logging
from typing import List, Dict, Any, Tuple
from core.supabase_client import SupabaseManager
from core.adspower_api import AdsPowerAPI
from core.path_utils import user_data_path

# Silence verbose HTTP logs from external libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("postgrest").setLevel(logging.WARNING)

# Constant definition of limits per plan
PLAN_LIMITS = {
    "START": {
        "max_profiles": 5,
        "active_profiles_per_day": (4, 5),
        "session_time": (10, 15)
    },
    "SCALE": {
        "max_profiles": 100,
        "active_profiles_per_day": (50, 100),
        "session_time": (5, 60)
    },
    "TEAM": {
        "max_profiles": 1000,
        "active_profiles_per_day": (100, 1000),
        "session_time": (1, 120)
    }
}


class PlanManager:
    def __init__(self, config_dir: str = "config"):
        self.usage_file = user_data_path(os.path.join(config_dir, "daily_usage.json"))
        os.makedirs(os.path.dirname(self.usage_file), exist_ok=True)
        self.supabase = SupabaseManager()
        self.adspower = AdsPowerAPI()
        
        # Caching
        self._last_manual_usage_check = 0.0
        self._cached_manual_opens_count = 0
        
        # User Plan Cache: token -> (timestamp, data)
        self._plan_cache = {}
        self._plan_cache_ttl = 60 # 60 seconds cache
        self._last_token = None

        
    def _get_today_str(self) -> str:
        return datetime.date.today().isoformat()
        
    def _load_daily_usage(self) -> Dict:
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, "r") as f:
                    data = json.load(f)
                    if data.get("date") == self._get_today_str():
                        return data
            except Exception:
                pass
        
        # Reset for today
        return {
            "date": self._get_today_str(),
            "automated_opens": [], # List of profile IDs run by automation today
            "failed_profiles": []
        }
        
    def _save_daily_usage(self, data: Dict):
        with open(self.usage_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_user_plan_config(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch plan from Supabase and merge with limits.
        Uses a 60-second cache to prevent spamming Supabase.
        """
        now = time.time()
        
        # Reset cache completely if token changed
        if access_token != self._last_token:
            self._plan_cache = {}
            self._last_token = access_token

        if access_token and access_token in self._plan_cache:
            last_check, cached_data = self._plan_cache[access_token]
            if now - last_check < self._plan_cache_ttl:
                return cached_data

        if not access_token:
            plan_name = "START"
            safety_limit = 50
            print("    [PlanManager] No access token provided, defaulting to START.")
        else:
            plan_data = self.supabase.get_user_plan(access_token)
            if not plan_data:
                plan_name = "START"
                safety_limit = 50
                print(f"    [PlanManager] No plan data found for token, defaulting to START.")
            else:
                plan_name = str(plan_data.get("plan", "START")).strip().upper()
                safety_limit = plan_data.get("adspower_limit", 50)
                status = plan_data.get("status", "unknown")

        if plan_name not in PLAN_LIMITS:
            plan_name = "START"
            
        limits = PLAN_LIMITS[plan_name]
        config = {
            "plan": plan_name,
            "max_profiles": limits["max_profiles"],
            "active_profiles_per_day": limits["active_profiles_per_day"],
            "session_time": limits["session_time"],
            "adspower_safety_limit": safety_limit
        }

        # Update cache
        if access_token:
            self._plan_cache[access_token] = (now, config)
            
        return config

        
    def check_manual_usage(self) -> int:
        """
        Poll AdsPower profiles to calculate manual usage today.
        Manual usage = Opened today AND NOT in our automated_opens list.
        Uses a 60-second cache to prevent AdsPower 'Too many requests' error.
        """
        import time
        now = time.time()
        if now - self._last_manual_usage_check < 60.0:
            return self._cached_manual_opens_count

        profiles = self.adspower.list_profiles()
        usage_data = self._load_daily_usage()
        automated = set(usage_data["automated_opens"])
        
        today_str = self._get_today_str()
        manual_opens_count = 0
        
        for p in profiles:
            # "last_open_time" may be a timestamp or a formatted string depending on AdsPower API version
            last_open = p.get("last_open_time") 
            if not last_open:
                continue
                
            pid = p.get("user_id")
            
            # Simple substring check or format check
            # For AdsPower, normally it's Unix timestamp, sometimes formatted.
            # Assuming unix timestamp or similar format with 'yyyy-mm-dd'
            opened_today = False
            if isinstance(last_open, (int, float)):
                # seconds unix time
                dt = datetime.datetime.fromtimestamp(int(last_open))
                if dt.date() == datetime.date.today():
                    opened_today = True
            elif isinstance(last_open, str):
                if today_str in last_open:
                    opened_today = True
            
            if opened_today and pid not in automated:
                manual_opens_count += 1
                
        self._cached_manual_opens_count = manual_opens_count
        self._last_manual_usage_check = now
        return manual_opens_count

    def get_status(self, access_token: str) -> Dict:
        """
        Returns full status of daily limits and capacities.
        """
        config = self.get_user_plan_config(access_token)
        usage_data = self._load_daily_usage()
        automated_opened = len(usage_data["automated_opens"])
        
        manual_opens = self.check_manual_usage()
        
        # Calculate Automation Available Capacity
        # Total daily safe limit = AdsPower Safety * 60%
        adspower_safety = config["adspower_safety_limit"]
        safe_total = int(adspower_safety * 0.6)
        
        used_total = manual_opens + automated_opened
        remaining = max(0, safe_total - used_total)
        
        return {
            "plan": config["plan"],
            "limits": config,
            "usage": {
                "automated_opens": usage_data["automated_opens"],
                "automated_opened_count": automated_opened,
                "manual_opens": manual_opens,
                "total_used": used_total,
                "remaining_safe_capacity": remaining,
                "total_safe_capacity": safe_total,
                "ran_profiles": usage_data["automated_opens"]
            }
        }
        
    def log_profile_opened(self, profile_id: str):
        usage = self._load_daily_usage()
        if profile_id not in usage["automated_opens"]:
            usage["automated_opens"].append(profile_id)
            self._save_daily_usage(usage)

    def log_profile_failed(self, profile_id: str):
        usage = self._load_daily_usage()
        if profile_id not in usage["failed_profiles"]:
            usage["failed_profiles"].append(profile_id)
            self._save_daily_usage(usage)

    def select_profiles(self, available_profiles: List[Dict], access_token: str) -> Tuple[List[str], List[Dict]]:
        """
        Enforce plan-based limits on profile selection.
        """
        status = self.get_status(access_token)
        plan_name = status["plan"]
        max_limit = status["limits"]["max_profiles"]
        
        selected_ids = []
        skipped_info = []
        
        for i, p in enumerate(available_profiles):
            if len(selected_ids) < max_limit:
                selected_ids.append(p["id"])
            else:
                skipped_info.append({
                    "id": p["id"],
                    "reason": f"Limite do plano {plan_name} atingido ({max_limit} perfis)"
                })
        
        if skipped_info:
            print(f"    [Plano: {plan_name}] Limitando execução a {max_limit} perfis (Ignorados: {len(skipped_info)})")
        else:
            print(f"    [Plano: {plan_name}] Executando {len(selected_ids)} perfis.")
                
        return selected_ids, skipped_info

