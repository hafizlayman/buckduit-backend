from flask import Blueprint, request, jsonify
from ai.policy_action_engine import process_event

policy_bp = Blueprint("policy", __name__)

@policy_bp.route("/trigger", methods=["POST"])
def trigger_event():
    data = request.get_json()
    event_type = data.get("event_type")
    payload = data.get("payload", {})
    process_event(event_type, payload)
    return jsonify({"status": "ok", "message": "Event processed"}), 200
