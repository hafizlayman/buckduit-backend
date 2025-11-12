import os
from supabase import create_client, Client


_SUPABASE_URL = os.getenv("SUPABASE_URL")
_SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")


if not _SUPABASE_URL or not _SUPABASE_SERVICE_KEY:
raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY/ANON_KEY in environment")


supabase: Client = create_client(_SUPABASE_URL, _SUPABASE_SERVICE_KEY)