import json
import re
from datetime import datetime, timedelta, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.database import database

_PARAM_RE = re.compile(r"/\d+(?=/|$)")

def _normalize(path: str) -> str:
    return _PARAM_RE.sub("/{id}", path)

class ApiLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        response = await call_next(request)
        path = request.url.path
        if not path.startswith("/api/"):
            return response
        method = request.method
        endpoint = _normalize(path)
        payload_bytes = len(body)
        caller_ip = request.client.host if request.client else "unknown"
        status_code = response.status_code
        now = datetime.now(timezone.utc)
        try:
            database.api_request_logs.insert_one({"method": method, "endpoint": endpoint, "status_code": status_code, "payload_bytes": payload_bytes, "caller_ip": caller_ip, "requested_at": now})
            query = {"method": method, "endpoint": endpoint}
            recent = database.api_request_logs.count_documents({**query, "requested_at": {"$gte": now - timedelta(minutes=1)}})
            average = list(database.api_request_logs.aggregate([{"$match": query}, {"$group": {"_id": None, "average": {"$avg": "$payload_bytes"}}}]))
            callers = database.api_request_logs.distinct("caller_ip", query)
            database.api_endpoint_stats.update_one(query, {"$inc": {"total_calls": 1}, "$set": {"rpm": float(recent), "avg_payload_bytes": float(average[0]["average"]) if average else 0.0, "unique_callers": json.dumps(sorted(callers)), "last_updated": now}, "$setOnInsert": {"method": method, "endpoint": endpoint}}, upsert=True)
        except Exception:
            pass
        return response

