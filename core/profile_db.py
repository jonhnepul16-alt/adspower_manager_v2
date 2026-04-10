import os
import json
from typing import List, Dict, Optional

class ProfileDB:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        self.db_file = os.path.join(self.config_dir, "profiles.json")
        
    def _read_db(self) -> List[Dict]:
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _write_db(self, profiles: List[Dict]):
        with open(self.db_file, "w") as f:
            json.dump(profiles, f, indent=2)
            
    def get_all(self) -> List[Dict]:
        return self._read_db()
        
    def get_by_id(self, profile_id: str) -> Optional[Dict]:
        for p in self._read_db():
            if p["id"] == profile_id:
                return p
        return None

    def add_profile(self, profile_id: str, name: str, tag: str = "") -> bool:
        profiles = self._read_db()
        # Avoid duplicate
        if any(p["id"] == profile_id for p in profiles):
            return False
            
        profiles.append({
            "id": profile_id,
            "name": name,
            "tag": tag,
            "imported_at": __import__("datetime").date.today().isoformat(),
            "history": []
        })
        self._write_db(profiles)
        return True

    def remove_profile(self, profile_id: str) -> bool:
        profiles = self._read_db()
        filtered = [p for p in profiles if p["id"] != profile_id]
        if len(filtered) < len(profiles):
            self._write_db(filtered)
            return True
        return False

    def update_profile(self, profile_id: str, name: str, tag: str) -> bool:
        profiles = self._read_db()
        for p in profiles:
            if p["id"] == profile_id:
                p["name"] = name
                p["tag"] = tag
                self._write_db(profiles)
                return True
        return False

    def add_history(self, profile_id: str, date_str: str, duration: int) -> bool:
        profiles = self._read_db()
        for p in profiles:
            if p["id"] == profile_id:
                if "history" not in p:
                    p["history"] = []
                p["history"].append({
                    "date": date_str,
                    "duration": duration
                })
                # Opcional: Manter apenas os ultimos 30 logs para não pesar muito
                p["history"] = p["history"][-30:]
                self._write_db(profiles)
                return True
        return False
