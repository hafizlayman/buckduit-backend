# ai_telemetry.py
import os, time
from datetime import datetime, timezone
from typing import Optional, Tuple
from supabase import Client, create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

def supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Supabase not initialized — missing URL or Key")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def ensure_tables(sb: Client) -> None:
    """
    Idempotent: creates ai_core_status table if missing (RPC-less fallback).
    You already created this earlier, but keeping a guard avoids hard crashes on fresh envs.
    """
    try:
        # lightweight check
        sb.table("ai_core_status").select("id").limit(1).execute()
    except Exception:
        # Try to create minimal table via SQL (requires service role).
        # If policies block, you’ll see an error in logs but main loop will continue.
        sql = """
        create table if not exists public.ai_core_status (
          id bigint primary key,
          status text,
          last_heartbeat timestamptz,
          error text,
          updated_at timestamptz default now()
        );
        """
        try:
            sb.postgrest.rpc("exec_sql", {"sql": sql}).execute()  # if you added a helper RPC
        except Exception:
            # Silent: table likely exists or RPC not present. Safe to proceed.
            pass

def heartbeat_upsert(sb: Client, node_id: int, status: str = "ok", err: Optional[str] = None) -> None:
    now = iso_now()
    payload = {
        "id": node_id,
        "status": status,
        "last_heartbeat": now,
        "error": err or None,
        "updated_at": now,
    }
    sb.table("ai_core_status").upsert(payload).execute()

def get_last_heartbeat(sb: Client, node_id: int) -> Tuple[Optional[str], Optional[str]]:
    """Returns (iso_timestamp, status) or (None, None) if missing."""
    res = sb.table("ai_core_status").select("last_heartbeat,status").eq("id", node_id).limit(1).execute()
    if res.data:
        row = res.data[0]
        return row.get("last_heartbeat"), row.get("status")
    return None, None
