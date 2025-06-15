import pytest
import time
import threading
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cache import ThreadSafeLRUCache

@pytest.fixture
def cache():
    """Create a fresh cache instance for each test"""
    cache = ThreadSafeLRUCache(max_size=5)
    yield cache
    cache.clear()

class TestBasicOperations:
    def test_put_get(self, cache):
        """Test basic put and get operations"""
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None

    def test_delete(self, cache):
        """Test delete operation"""
        cache.put("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None
        # Deleting non-existent key should not raise error
        cache.delete("nonexistent")

    def test_clear(self, cache):
        """Test clear operation"""
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get_stats()["current_size"] == 0

    def test_get_all(self, cache):
        """Test get_all operation"""
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        all_items = cache.get_all()
        assert len(all_items) == 2
        assert any(item["key"] == "key1" and item["value"] == "value1" for item in all_items)
        assert any(item["key"] == "key2" and item["value"] == "value2" for item in all_items)

class TestTTL:
    def test_default_ttl(self, cache):
        """Test default TTL expiration"""
        cache = ThreadSafeLRUCache(max_size=5, default_ttl=1)
        cache.put("key1", "value1")
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_custom_ttl(self, cache):
        """Test custom TTL for specific items"""
        cache.put("key1", "value1", ttl=1)
        cache.put("key2", "value2", ttl=2)
        time.sleep(1.1)
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        time.sleep(1)
        assert cache.get("key2") is None

    def test_no_ttl(self, cache):
        """Test items with no TTL"""
        cache.put("key1", "value1", ttl=None)
        time.sleep(1)
        assert cache.get("key1") == "value1"

class TestLRUEviction:
    def test_eviction_order(self, cache):
        """Test LRU eviction order"""
        # Fill cache to capacity
        for i in range(5):
            cache.put(f"key{i}", f"value{i}")
        
        # Access key0 to make it most recently used
        cache.get("key0")
        
        # Add new item, should evict key1 (least recently used)
        cache.put("key5", "value5")
        assert cache.get("key1") is None
        assert cache.get("key0") == "value0"  # Should still be there
        assert cache.get("key5") == "value5"

    def test_access_updates_lru(self):
        """Test that accessing an item updates its LRU status in a size‑2 cache"""
        small_cache = ThreadSafeLRUCache(max_size=2)
        small_cache.put("key1", "value1")
        small_cache.put("key2", "value2")
        # Both slots are full; touch key1 to make it MRU
        assert small_cache.get("key1") == "value1"
        # Insert a third; should evict key2 (the LRU)
        small_cache.put("key3", "value3")
        # key2 is gone, key1 and key3 remain
        assert small_cache.get("key2") is None
        assert small_cache.get("key1") == "value1"
        assert small_cache.get("key3") == "value3"

class TestConcurrentAccess:
    def test_concurrent_puts(self, cache):
        """Test concurrent put operations"""
        def put_items():
            for i in range(100):
                cache.put(f"key{i}", f"value{i}")

        threads = [threading.Thread(target=put_items) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Verify no data corruption
        all_items = cache.get_all()
        assert len(all_items) <= cache.max_size
        for item in all_items:
            assert item["value"] == f"value{item['key'][3:]}"

    def test_concurrent_gets(self, cache):
        """Test concurrent get operations"""
        # Setup some initial data
        for i in range(5):
            cache.put(f"key{i}", f"value{i}")

        def get_items():
            for _ in range(100):
                for i in range(5):
                    value = cache.get(f"key{i}")
                    assert value is None or value == f"value{i}"

        threads = [threading.Thread(target=get_items) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

class TestStatistics:
    def test_basic_stats(self, cache):
        """Test basic statistics tracking"""
        cache.put("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["total_requests"] == 2
        assert stats["hit_rate"] == 0.5

    def test_eviction_stats(self, cache):
        """Test eviction statistics"""
        # Fill cache to capacity
        for i in range(6):  # One more than max_size
            cache.put(f"key{i}", f"value{i}")
        stats = cache.get_stats()
        assert stats["evictions"] == 1
        assert stats["current_size"] == 5

    def test_expiration_stats(self, cache):
        """Test expiration statistics"""
        cache = ThreadSafeLRUCache(max_size=5, default_ttl=1)
        cache.put("key1", "value1")
        time.sleep(1.1)
        cache.get("key1")  # Should count as a miss and trigger expiration
        stats = cache.get_stats()
        assert stats["expired_removals"] == 1
        assert stats["misses"] == 1
