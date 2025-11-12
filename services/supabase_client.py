# services/supabase_client.py
from supabase import create_client, Client
import os


_SUPABASE: Client | None = None


def get_client() -> Client:
global _SUPABASE
if _SUPABASE is None:
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
if not url or not key:
raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY are required")
_SUPABASE = create_client(url, key)
return _SUPABASE