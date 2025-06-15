from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Any
from cache import ThreadSafeLRUCache
import os
import time

app = FastAPI()
cache = ThreadSafeLRUCache(max_size=1000, default_ttl=60)

class PutRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = None

@app.get("/")
def serve_ui():
    # Serve the HTML UI from the same server
    ui_path = os.path.join(os.path.dirname(__file__), "cache_ui.html")
    return FileResponse(ui_path, media_type="text/html")

@app.post("/put")
def put_item(req: PutRequest):
    cache.put(req.key, req.value, req.ttl)
    return {"status": "ok"}

@app.get("/get")
def get_item(key: str):
    value = cache.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found or expired")
    return {"key": key, "value": value}

@app.delete("/delete")
def delete_item(key: str):
    cache.delete(key)
    return {"status": "deleted"}

@app.post("/clear")
def clear_cache():
    cache.clear()
    return {"status": "cleared"}

@app.get("/stats")
def get_stats():
    return cache.get_stats()

@app.get("/all")
def get_all():
    # Return all keys and their values (non-expired only)
    result = []
    with cache.lock:
        for key, node in cache.cache.items():
            if node.expire_at is None or node.expire_at > time.time():
                result.append({"key": key, "value": node.value})
    return result 