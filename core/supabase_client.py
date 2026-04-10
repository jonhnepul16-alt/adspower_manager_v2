import os
from supabase import create_client, Client
from typing import Optional, Dict

class SupabaseManager:
    def __init__(self):
        self.url: str = os.environ.get("SUPABASE_URL", "https://mewueckdincysvdhfxbp.supabase.co")
        self.key: str = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ld3VlY2tkaW5jeXN2ZGhmeGJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2MTg3MzYsImV4cCI6MjA5MTE5NDczNn0.QjH55p0S3GOsNRZLtxomcFekfEpFqY2TnUqP561biG8")

        
        # Override with real credentials if passed through environment via Electron
        if not self.url.startswith("http"):
            print("[WARN] Supabase URL is not proper HTTP. Check environment variables.")
            
        try:
            self.client: Client = create_client(self.url, self.key)
        except Exception as e:
            print(f"[WARN] Failed to init Supabase client: {e}")
            self.client = None

    def get_user_plan(self, access_token: str) -> Optional[Dict]:
        """
        Fetches the user's subscription record using their authentication access token.
        """
        if not self.client:
            return None
            
        try:
            # Reconstruct the client strictly context for the user 
            # We use the token to identify the user first
            response = self.client.auth.get_user(access_token)
            if not response or not response.user:
                return None
            
            user_email = response.user.email
            
            # CRITICAL: We need to pass the access_token in the table query to respect RLS
            # In supabase-py v2, we can't easily set a persistent header per request in a shared client,
            # but we can create a temporary client or just rely on the service role if RLS is an issue.
            # However, for local desktop, querying by email is safe if RLS allows it.
            
            # Attempt to query with the user context (this handles RLS if policy allows 'select for authenticated')
            sub_resp = self.client.postgrest.auth(access_token).table("subscriptions").select("*").eq("email", user_email).execute()
            
            plan_data = {"plan": "START", "email": user_email, "adspower_limit": 50}
            
            status = "unknown"
            if sub_resp.data and len(sub_resp.data) > 0:
                record = sub_resp.data[0]
                status = record.get("status", "unknown")
                tier = record.get("tier", "START").upper()
                is_premium = record.get("is_premium", False)
                adspower_limit = record.get("adspower_limit", 50)
                
                # If they are premium but tier isn't fully defined, default gracefully
                if is_premium and tier == "START":
                    tier = "SCALE" 
                
                plan_data["plan"] = tier if status == "active" else "START"
                plan_data["adspower_limit"] = adspower_limit
            
            print(f"    [Supabase] Plano detectado para {user_email}: {plan_data['plan']} (Status: {status})")
            return plan_data




        except Exception as e:
            print(f"Error fetching plan from Supabase: {e}")
            return None
