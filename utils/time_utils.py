from datetime import datetime, timezone

def utcnow():
    """Return UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)

def to_iso(dt):
    """Convert datetime to ISO string in UTC."""
    return dt.astimezone(timezone.utc).isoformat()
