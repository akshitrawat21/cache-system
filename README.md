# Thread-Safe In-Memory Cache System

A production-ready, thread-safe in-memory cache system with LRU eviction, TTL support, and performance tracking.

## 🌐 Live Demo

Try out the cache system at: [https://cache-system.onrender.com/](https://cache-system.onrender.com/)

## Features

- *Thread-Safe Operations*: Concurrent access support with proper synchronization
- *LRU Eviction*: Automatic removal of least recently used items when cache is full
- *TTL Support*: Automatic expiration of cache entries with configurable time-to-live
- *Performance Tracking*: Detailed statistics including hits, misses, and evictions
- *Web Interface*: User-friendly UI for cache operations
- *REST API*: Full HTTP API for programmatic access

## Development Setup

### Prerequisites
- Python 3.11.7
- pip (Python package installer)

1. *Create and Activate Virtual Environment*

   bash
   # Create virtual environment with Python 3.13.1
   python3.11 -m venv venv

   # Activate virtual environment
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On Unix/MacOS:
   source venv/bin/activate
   

2. *Install Dependencies*

   bash
   pip install -r requirements.txt
   

3. *Run the Server*

   bash
   uvicorn cache_api:app --reload
   

   The server will start at http://localhost:8000

4. *Access the Web Interface*

   Open http://localhost:8000 in your browser to access the web interface.

## Installation

1. Clone the repository:
bash
git clone https://github.com/akshitrawat21/cache-system
cd cache_system


2. Follow the Development Setup steps above.

## Usage

### Web Interface

Open http://localhost:8000 in your browser to access the web interface. You can:
- Add/update cache entries
- Retrieve values
- Delete entries
- View all entries
- Monitor cache statistics

### API Endpoints

- GET /: Web interface
- POST /put: Add/update a cache entry
  json
  {
    "key": "user:123",
    "value": "John Doe",
    "ttl": 300  // optional, in seconds
  }
  
- GET /get?key=user:123: Retrieve a value
- DELETE /delete?key=user:123: Remove an entry
- POST /clear: Clear all entries
- GET /stats: Get cache statistics
- GET /all: List all non-expired entries

### Python API

python
from cache import ThreadSafeLRUCache

# Create cache with max 1000 entries and 5-minute default TTL
cache = ThreadSafeLRUCache(max_size=1000, default_ttl=300)

# Store data
cache.put("user:123", "John Doe", ttl=600)

# Retrieve data
value = cache.get("user:123")

# Get statistics
stats = cache.get_stats()


## Design Decisions

### Concurrency Model
- Uses threading.RLock() for thread-safe operations
- Minimizes lock contention by using fine-grained locking
- Background cleanup thread for expired entries

### Eviction Logic
- LRU (Least Recently Used) eviction policy
- O(1) time complexity for eviction operations
- Automatic eviction when cache size exceeds max_size

### Performance Considerations
- O(1) time complexity for get/put operations
- Efficient memory usage with doubly linked list
- Background cleanup to prevent memory leaks
- Minimal lock contention for better concurrency

## Testing

Run the test suite:
bash
pytest test_cache.py


Test coverage includes:
- Basic operations (put/get/delete)
- TTL expiration
- LRU eviction
- Concurrent access
- Edge cases

## Sample Statistics Output

json
{
    "hits": 150,
    "misses": 25,
    "hit_rate": 0.857,
    "total_requests": 175,
    "current_size": 45,
    "evictions": 12,
    "expired_removals": 8
}


## Error Handling

The system handles various error cases:
- Invalid keys
- Expired entries
- Concurrent access conflicts
- Cache size limits
