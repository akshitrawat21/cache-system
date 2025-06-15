from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from cache import ThreadSafeLRUCache
import pytest
import sys
import io
import os
from contextlib import redirect_stdout
import json
from datetime import datetime

app = FastAPI(title="Thread-Safe LRU Cache API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize cache with a reasonable size
cache = ThreadSafeLRUCache(max_size=1000)

# Mount static files
app.mount("/", StaticFiles(directory=".", html=True), name="static")

@app.post("/put")
async def put_item(key: str, value: str, ttl: int = None):
    """Put an item in the cache with optional TTL (seconds)"""
    cache.put(key, value, ttl)
    return {"status": "success", "message": f"Item {key} stored"}

@app.get("/get")
async def get_item(key: str):
    """Get an item from the cache by key"""
    value = cache.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Key {key} not found or expired")
    return {"key": key, "value": value}

@app.delete("/delete")
async def delete_item(key: str):
    """Delete an item from the cache by key"""
    cache.delete(key)
    return {"status": "success", "message": f"Item {key} deleted"}

@app.post("/clear")
async def clear_cache():
    """Clear all items from the cache"""
    cache.clear()
    return {"status": "success", "message": "Cache cleared"}

@app.get("/stats")
async def get_stats():
    """Get cache statistics"""
    stats = cache.get_stats()
    return {
        "hits": stats["hits"],
        "misses": stats["misses"],
        "hit_rate": stats["hit_rate"],
        "total_requests": stats["total_requests"],
        "current_size": stats["current_size"],
        "evictions": stats["evictions"],
        "expired_removals": stats["expired_removals"]
    }

@app.get("/all")
async def get_all():
    """Get all non-expired items in the cache"""
    return cache.get_all()

@app.get("/run-tests")
async def run_tests():
    """Run all test cases and return results"""
    try:
        # Get the absolute path to the test file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_file = os.path.join(current_dir, "test_cache.py")
        
        if not os.path.exists(test_file):
            return JSONResponse(
                status_code=404,
                content={"error": f"Test file not found at {test_file}"}
            )

        # Capture pytest output
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            # Run pytest with specific test file
            result = pytest.main(["-v", test_file])
        
        # Parse test results
        output_lines = captured_output.getvalue().split('\n')
        test_results = []
        
        for line in output_lines:
            if line.startswith('test_'):
                parts = line.split()
                if len(parts) >= 2:
                    test_name = parts[0]
                    status = 'passed' if 'PASSED' in line else 'failed' if 'FAILED' in line else 'skipped'
                    message = ' '.join(parts[1:]) if len(parts) > 1 else None
                    
                    test_results.append({
                        "name": test_name,
                        "status": status,
                        "message": message
                    })
        
        if not test_results:
            test_results.append({
                "name": "No tests found",
                "status": "skipped",
                "message": "No test cases were found in the test file"
            })
        
        return JSONResponse(content=test_results)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error running tests: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 