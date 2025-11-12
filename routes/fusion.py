from flask import Blueprint, jsonify, request
from supabase import create_client
import os

fusion_bp = Blueprint("fusion_bp", __name__)

from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

@fusion_bp.route("/offers", methods=["GET"])
def get_fused_offers():
    try:
        category = request.args.get("category")
        country = request.args.get("country")
        min_rating = request.args.get("min_rating")

        params = {
            "p_category": category if category else None,
            "p_country": country if country else None,
            "p_min_rating": float(min_rating) if min_rating else None,
        }

        response = supabase.rpc("get_fused_offers", params=params).execute()
        return jsonify({"status": "success", "data": response.data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@fusion_bp.route("/refresh", methods=["POST"])
def refresh_fused_kpis():
    try:
        supabase.rpc("refresh_fused_kpis").execute()
        return jsonify({"status": "success", "message": "KPIs refreshed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
