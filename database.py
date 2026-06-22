from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

class DB:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def save_lead(self, company: str, site: str = None, phone: str = None, email: str = None, source: str = "yandex"):
        data = {
            "company": company,
            "site": site,
            "phone": phone,
            "email": email,
            "source": source,
            "status": "new",
            "created_at": "now()"
        }
        return self.supabase.table("leads").insert(data).execute()
    
    def get_new_leads(self, limit=30):
        response = self.supabase.table("leads").select("*").eq("status", "new").limit(limit).execute()
        return response.data
