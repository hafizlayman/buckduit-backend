# =========================================
# backend/routes/auto_tuner.py
# Stage 13.93 — Auto-Tuner Controls (v1.1)
# =========================================
from flask import Blueprint, jsonify, request
from supabase import create_client
import os
from datetime import datetime

tuner_state_bp = Blueprint("tuner_state_bp", __name__)

# ---------- Supabase ----------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # use service role in backend
supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected (auto_tuner)")
    else:
        print("⚠️ Missing Supabase credentials (auto_tuner).")
except Exception as e:
    print(f"❌ Supabase init failed (auto_tuner): {e}")

# ---------- Helpers ----------
def _clamp(v, lo, hi):
    try:
        v = float(v)
        return max(lo, min(hi, v))
    except Exception:
        return None

def _ensure_row():
    """Make sure there is exactly one row; return it."""
    if not supabase:
        return None, "Supabase not initialized"

    # Try to fetch the latest state (id desc)
    res = supabase.table("auto_tuner_state").select("*").order("id", desc=True).limit(1).execute()
    rows = res.data or []
    if rows:
        return rows[0], None

    # Seed if empty
    insert = supabase.table("auto_tuner_state").insert({
        "target_accuracy": 0.92,
        "max_bias": 0.15,
        "learning_rate": 0.05,
        "correction_weight": 0.50,
        "notes": "seeded by backend",
    }).execute()
    seeded = (insert.data or [None])[0]
    return seeded, None

# ---------- Routes ----------
@tuner_state_bp.route("/tuner-state", methods=["GET"])
def get_tuner_state():
    """Return current tuner state (creates one if absent)."""
    try:
        row, err = _ensure_row()
        if err:
            return jsonify({"error": err}), 500
        return jsonify({"status": "ok", "state": row}), 200
    except Exception as e:
        print(f"❌ tuner-state GET error: {e}")
        return jsonify({"error": str(e)}), 500

@tuner_state_bp.route("/tuner-state", methods=["POST"])
def set_tuner_state():
    """
    Accepts JSON with any of:
      - target_accuracy (0.50..0.999)
      - max_bias       (0.00..0.50)
      - learning_rate  (0.001..0.50)
      - correction_weight (0.00..1.00)
      - notes (string)
    Upserts into the single-row table.
    """
    try:
        if not supabase:
            return jsonify({"error": "Supabase not initialized"}), 500

        payload = request.get_json(force=True, silent=True) or {}
        row, err = _ensure_row()
        if err:
            return jsonify({"error": err}), 500

        # Current values as defaults
        new_state = {
            "target_accuracy": row.get("target_accuracy", 0.92),
            "max_bias": row.get("max_bias", 0.15),
            "learning_rate": row.get("learning_rate", 0.05),
            "correction_weight": row.get("correction_weight", 0.50),
            "notes": row.get("notes", ""),
        }

        if "target_accuracy" in payload:
            val = _clamp(payload["target_accuracy"], 0.50, 0.999)
            if val is None:
                return jsonify({"error": "Invalid target_accuracy"}), 400
            new_state["target_accuracy"] = val

        if "max_bias" in payload:
            val = _clamp(payload["max_bias"], 0.0, 0.50)
            if val is None:
                return jsonify({"error": "Invalid max_bias"}), 400
            new_state["max_bias"] = val

        if "learning_rate" in payload:
            val = _clamp(payload["learning_rate"], 0.001, 0.50)
            if val is None:
                return jsonify({"error": "Invalid learning_rate"}), 400
            new_state["learning_rate"] = val

        if "correction_weight" in payload:
            val = _clamp(payload["correction_weight"], 0.0, 1.0)
            if val is None:
                return jsonify({"error": "Invalid correction_weight"}), 400
            new_state["correction_weight"] = val

        if "notes" in payload and isinstance(payload["notes"], str):
            new_state["notes"] = payload["notes"][:500]

        new_state["updated_at"] = datetime.utcnow().isoformat() + "Z"

        # Upsert by id (use the existing row id)
        upsert = supabase.table("auto_tuner_state").update(new_state).eq("id", row["id"]).execute()
        saved = (upsert.data or [new_state])[0]

        # (Optional) Could notify a worker / set a flag for recalibration here
        return jsonify({"status": "ok", "state": saved}), 200

    except Exception as e:
        print(f"❌ tuner-state POST error: {e}")
        return jsonify({"error": str(e)}), 500

@tuner_state_bp.route("/tuner-recalibrate", methods=["POST"])
def trigger_recalibration():
    """
    Lightweight trigger endpoint for your adaptive engine.
    For now it just returns a simple OK; wire this to your worker if needed.
    """
    try:
        # In future: write a 'recalibrate' flag to a control table or file.
        return jsonify({"status": "ok", "message": "Recalibration signal accepted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
