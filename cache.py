import threading
import time
from typing import Any, Optional, Dict

class Node:
    """
    Doubly linked list node for LRU tracking.
    """
    def __init__(self, key: str, value: Any, expire_at: Optional[float]):
        self.key = key
        self.value = value
        self.expire_at = expire_at
        self.prev: Optional['Node'] = None
        self.next: Optional['Node'] = None

class ThreadSafeLRUCache:
    """
    Thread-safe in-memory cache with LRU eviction and TTL support.
    """
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None, cleanup_interval: int = 10):
        """
        Initialize the cache.
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self.lock = threading.RLock()
        self.cache: Dict[str, Node] = {}
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self.size = 0
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0,
            'evictions': 0,
            'expired_removals': 0
        }
        self._stop_event = threading.Event()
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired_keys, daemon=True)
        self._cleanup_thread.start()

    def put(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Store a key-value pair with optional TTL (in seconds).
        """
        expire_at = None
        if ttl is not None:
            expire_at = time.time() + ttl
        elif self.default_ttl is not None:
            expire_at = time.time() + self.default_ttl
        with self.lock:
            node = self.cache.get(key)
            if node:
                node.value = value
                node.expire_at = expire_at
                self._move_to_head(node)
            else:
                # If cache is full, evict LRU item before adding new one
                if self.size >= self.max_size:
                    self._evict_lru()
                new_node = Node(key, value, expire_at)
                self.cache[key] = new_node
                self._add_to_head(new_node)
                self.size += 1

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key and update access order.
        """
        with self.lock:
            self.stats['total_requests'] += 1
            node = self.cache.get(key)
            if not node:
                self.stats['misses'] += 1
                return None
            if node.expire_at is not None and node.expire_at < time.time():
                self._remove_node(node)
                self.stats['misses'] += 1
                self.stats['expired_removals'] += 1
                return None
            self._move_to_head(node)
            self.stats['hits'] += 1
            return node.value

    def delete(self, key: str):
        """
        Remove a key from cache.
        """
        with self.lock:
            node = self.cache.get(key)
            if node:
                self._remove_node(node)

    def clear(self):
        """
        Clear the entire cache.
        """
        with self.lock:
            self.cache.clear()
            self.head = None
            self.tail = None
            self.size = 0

    def get_stats(self) -> dict:
        """
        Return cache statistics.
        """
        with self.lock:
            total = self.stats['total_requests']
            hits = self.stats['hits']
            misses = self.stats['misses']
            hit_rate = hits / total if total > 0 else 0.0
            return {
                'hits': hits,
                'misses': misses,
                'hit_rate': round(hit_rate, 4),
                'total_requests': total,
                'current_size': self.size,
                'evictions': self.stats['evictions'],
                'expired_removals': self.stats['expired_removals']
            }

    def get_all(self):
        """
        Return all non-expired items as a list of dicts: {"key": ..., "value": ...}
        """
        with self.lock:
            now = time.time()
            result = []
            node = self.head
            while node:
                if node.expire_at is None or node.expire_at > now:
                    result.append({"key": node.key, "value": node.value})
                node = node.next
            return result

    def _evict_lru(self):
        """
        Evict the least recently used item.
        """
        if self.tail:
            self._remove_node(self.tail)
            self.stats['evictions'] += 1

    def _remove_node(self, node: Node):
        """
        Remove a node from the doubly linked list and cache dict.
        """
        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev
        if node == self.head:
            self.head = node.next
        if node == self.tail:
            self.tail = node.prev
        node.prev = node.next = None
        if node.key in self.cache:
            del self.cache[node.key]
            self.size -= 1

    def _add_to_head(self, node: Node):
        """
        Add a node to the head (most recently used) of the list.
        """
        node.prev = None
        node.next = self.head
        if self.head:
            self.head.prev = node
        self.head = node
        if not self.tail:
            self.tail = node

    def _move_to_head(self, node: Node):
        """
        Move a node to the head (most recently used).
        """
        if node == self.head:
            return
        # Remove from current position
        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev
        if node == self.tail:
            self.tail = node.prev
        # Add to head
        node.prev = None
        node.next = self.head
        if self.head:
            self.head.prev = node
        self.head = node

    def _cleanup_expired_keys(self):
        """
        Background thread to clean up expired keys.
        """
        while not self._stop_event.is_set():
            with self.lock:
                now = time.time()
                node = self.tail
                while node:
                    prev = node.prev
                    if node.expire_at is not None and node.expire_at < now:
                        self._remove_node(node)
                        self.stats['expired_removals'] += 1
                    node = prev
            self._stop_event.wait(self.cleanup_interval)

    def stop_cleanup_thread(self):
        """
        Stop the background cleanup thread (for testing/teardown).
        """
        self._stop_event.set()
        self._cleanup_thread.join() 