# ---------- Stage 14.02: log_route ----------
from functools import wraps
from flask import request
from utils.ai_logger import log_event

def log_route(source_name: str):
    """Wrap a Flask view to auto-log entry + exceptions."""
    def _outer(fn):
        @wraps(fn)
        def _inner(*args, **kwargs):
            try:
                log_event("INFO", source_name, f"hit {request.method} {request.path}",
                          meta={"args": kwargs, "query": request.args.to_dict(flat=True)})
                return fn(*args, **kwargs)
            except Exception as e:
                log_event("ERROR", source_name, f"route error: {e}",
                          meta={"path": request.path})
                raise
        return _inner
    return _outer
