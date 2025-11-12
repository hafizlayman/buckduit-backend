# =======================
# Alert Center API (Timeline + Stats)
# =======================
from datetime import timedelta
from flask import request

def _parse_range(range_str: str):
    # accepted: 24h, 7d, 30d, all
    if not range_str or range_str == "24h":
        return datetime.utcnow() - timedelta(hours=24)
    if range_str == "7d":
        return datetime.utcnow() - timedelta(days=7)
    if range_str == "30d":
        return datetime.utcnow() - timedelta(days=30)
    return None  # all

@app.route("/api/alerts/timeline", methods=["GET"])
def api_alerts_timeline():
    """
    Query unified timeline (alerts + system_logs view).
    Params:
      range=24h|7d|30d|all
      limit=integer (default 200)
    """
    try:
        rng = request.args.get("range", "24h")
        limit = int(request.args.get("limit", "200"))
        since = _parse_range(rng)

        if since:
            query = supabase.table("v_alert_timeline") \
                            .select("*") \
                            .gte("created_at", since.isoformat()) \
                            .order("created_at", desc=True) \
                            .limit(limit)
        else:
            query = supabase.table("v_alert_timeline") \
                            .select("*") \
                            .order("created_at", desc=True) \
                            .limit(limit)

        res = query.execute()
        rows = res.data or []
        return jsonify({"items": rows}), 200
    except Exception as e:
        print(f"⚠️ timeline error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/alerts/stats", methods=["GET"])
def api_alerts_stats():
    """
    Return counts by severity (and recent summary for header badges).
    Params:
      range=24h|7d|30d|all
    """
    try:
        rng = request.args.get("range", "24h")
        since = _parse_range(rng)

        if since:
            q = supabase.table("v_alert_timeline") \
                        .select("severity") \
                        .gte("created_at", since.isoformat())
        else:
            q = supabase.table("v_alert_timeline").select("severity")

        data = (q.execute().data) or []
        counts = {"info":0,"warning":0,"error":0,"critical":0}
        for r in data:
            sev = (r.get("severity") or "info").lower()
            if sev not in counts:
                counts[sev] = 0
            counts[sev] += 1

        # last alert preview (title+time)
        last_row = supabase.table("v_alert_timeline") \
                           .select("created_at,title,severity,category") \
                           .order("created_at", desc=True) \
                           .limit(1).execute().data
        last = last_row[0] if last_row else None
        return jsonify({"counts": counts, "last": last}), 200
    except Exception as e:
        print(f"⚠️ stats error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/alerts/test", methods=["POST"])
def api_alerts_test():
    """
    Quick manual insertion to alerts for testing UI.
    Body JSON: { "severity":"warning","title":"…","message":"…","category":"ai","meta":{...} }
    """
    try:
        payload = request.get_json(force=True) or {}
        row = {
            "severity": payload.get("severity","info"),
            "title": payload.get("title","Manual Test"),
            "message": payload.get("message","Triggered from /api/alerts/test"),
            "category": payload.get("category","system"),
            "source": "manual",
            "meta": payload.get("meta", {})
        }
        supabase.table("alerts").insert(row).execute()
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
