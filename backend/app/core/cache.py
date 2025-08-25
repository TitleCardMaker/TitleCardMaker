import asyncio
import threading
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable, TypeVar
from functools import wraps
import hashlib

from app.logging.logger import log

from app.schemas.schedule import Hours

if TYPE_CHECKING:
    from app.models.card import Card


T = TypeVar('T')

class CacheEntry:
    """Represents a single cache entry with metadata."""
    
    def __init__(self,
            value: Any,
            ttl: int,
            created_at: datetime | None = None,
        ) -> None:

        self.value = value
        self.ttl = ttl
        self.created_at = created_at or datetime.now()
        self.access_count = 0
        self.last_accessed = self.created_at


    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)


    @property
    def age(self) -> float:
        """Get the age of the cache entry in seconds."""
        return (datetime.now() - self.created_at).total_seconds()


    def access(self):
        """Mark the entry as accessed."""

        self.access_count += 1
        self.last_accessed = datetime.now()


class CacheStats:
    """Statistics for cache performance monitoring."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0


    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""

        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


    def reset(self):
        """Reset all statistics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0


class CacheManager:
    """
    Advanced in-memory cache manager with TTL, and eviction policies.
    """

    def __init__(self, 
            max_size: int = 1000,
            default_ttl: int = 3600,
        ) -> None:
        """
        Initialize the cache manager.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
        """

        self.max_size = max_size
        self.default_ttl = default_ttl

        # Cache storage
        self._cache: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

        # Statistics
        self.stats = CacheStats()

        # Cache invalidation patterns
        self._invalidation_patterns: dict[str, set[str]] = {}

        # Background cleanup task
        self._cleanup_task: asyncio.Task | None = None
        self._stop_cleanup = False


    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from function arguments."""
        # Create a deterministic string representation
        key_parts = []
        
        # Add positional arguments (excluding database session)
        for arg in args:
            # Skip database session objects
            if hasattr(arg, '__class__') and 'Session' in arg.__class__.__name__:
                continue
            key_parts.append(str(arg))

        # Add keyword arguments (sorted for consistency, excluding database session)
        for key, value in sorted(kwargs.items()):
            # Skip database session and logger objects
            if (key in ['db', 'log'] or (
                hasattr(value, '__class__')
                and 'Session' in value.__class__.__name__
            )):
                continue
            key_parts.append(f"{key}={value}")
        
        # Create hash of the combined string
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self.stats.misses += 1
                return default

            if entry.is_expired:
                del self._cache[key]
                self.stats.misses += 1
                return default

            # Mark as accessed
            entry.access()
            self.stats.hits += 1

            return entry.value


    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """

        try:
            with self._lock:
                # Check if we need to evict entries
                if len(self._cache) >= self.max_size:
                    self._evict_entries()

                # Set the cache entry
                ttl = ttl or self.default_ttl
                self._cache[key] = CacheEntry(value, ttl)
                self.stats.sets += 1

                # Add to invalidation patterns if key contains patterns
                self._add_to_invalidation_patterns(key)

                return True
        except Exception as e:
            log.error(f"Error setting cache key {key}: {e}")
            self.stats.errors += 1
            return False


    def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was found and deleted, False otherwise
        """

        with self._lock:
            if key in self._cache:
                log.trace(f'Removing {key} from cache')
                del self._cache[key]
                self.stats.deletes += 1

                return True

            return False


    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match (supports wildcards)
            
        Returns:
            Number of entries invalidated
        """

        with self._lock:
            invalidated = 0
            # Convert pattern to regex-like matching
            if '*' in pattern:
                import fnmatch
                keys_to_delete = [
                    key for key in self._cache.keys()
                    if fnmatch.fnmatch(key, pattern)
                ]
            else:
                keys_to_delete = [
                    key for key in self._cache.keys() if pattern in key
                ]

            for key in keys_to_delete:
                log.trace(f'Removing {key} from cache')
                del self._cache[key]
                invalidated += 1

            self.stats.deletes += invalidated

            return invalidated


    def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """

        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self.stats.deletes += count
            return count


    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""

        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'hit_rate': self.stats.hit_rate,
                'evictions': self.stats.evictions,
                'sets': self.stats.sets,
                'deletes': self.stats.deletes,
                'errors': self.stats.errors,
                'oldest_entry_age': self._get_oldest_entry_age(),
                'newest_entry_age': self._get_newest_entry_age(),
            }


    def _evict_entries(self) -> None:
        """Evict cache entries using LRU policy."""

        if not self._cache:
            return None

        # Sort by last accessed time (LRU)
        entries = sorted(
            self._cache.items(), key=lambda x: x[1].last_accessed
        )

        # Remove oldest 10% of entries
        to_remove = max(1, len(entries) // 10)

        for key, _ in entries[:to_remove]:
            del self._cache[key]
            self.stats.evictions += 1


    def _add_to_invalidation_patterns(self, key: str):
        """Add key to invalidation patterns for pattern-based invalidation."""

        for part in key.split('|'):
            if '=' in part:
                # This is a keyword argument, create pattern
                pattern = f'{part.split("=")[0]}=*'
                if pattern not in self._invalidation_patterns:
                    self._invalidation_patterns[pattern] = set()
                self._invalidation_patterns[pattern].add(key)
    

    def _get_oldest_entry_age(self) -> float:
        """Get age of oldest cache entry."""

        if not self._cache:
            return 0.0

        return min(entry.age for entry in self._cache.values())
    

    def _get_newest_entry_age(self) -> float:
        """Get age of newest cache entry."""

        if not self._cache:
            return 0.0

        return max(entry.age for entry in self._cache.values())


    async def _cleanup_expired_entries(self):
        """Background task to clean up expired entries."""

        while not self._stop_cleanup:
            try:
                with self._lock:
                    expired_keys = [
                        key for key, entry in self._cache.items()
                        if entry.is_expired
                    ]
                    
                    for key in expired_keys:
                        del self._cache[key]
                        self.stats.evictions += 1
                    
                    if expired_keys:
                        log.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                # Wait 5 minutes before next cleanup
                await asyncio.sleep(300)

            except Exception as e:
                log.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(60)
    
    def start_cleanup_task(self):
        """Start the background cleanup task."""

        if self._cleanup_task is None:
            self._stop_cleanup = False
            self._cleanup_task = asyncio.create_task(
                self._cleanup_expired_entries()
            )


    def stop_cleanup_task(self):
        """Stop the background cleanup task."""

        if self._cleanup_task:
            self._stop_cleanup = True
            self._cleanup_task.cancel()
            self._cleanup_task = None


    def __del__(self):
        """Cleanup on destruction."""

        self.stop_cleanup_task()


    def __str__(self) -> str:
        """String representation of the cache manager."""
        
        with self._lock:
            if not self._cache:
                return f"CacheManager(empty, max_size={self.max_size})"
            
            # Show first few items
            items_preview = []
            for i, (key, entry) in enumerate(self._cache.items()):
                if i >= 5:  # Limit to first 5 items
                    items_preview.append(
                        f"... and {len(self._cache) - 5} more items"
                    )
                    break
                age = entry.age
                items_preview.append(
                    f"'{key}' (age={age:.1f}s, accesses={entry.access_count})"
                )
            
            return (
                f'CacheManager({len(self._cache)}/{self.max_size} items: '
                f'{", ".join(items_preview)})'
            )


    def __repr__(self) -> str:
        """Detailed string representation of the cache manager."""
        
        with self._lock:
            if not self._cache:
                return (
                    f"CacheManager(max_size={self.max_size}, "
                    f"default_ttl={self.default_ttl}, empty)"
                )
            
            # Show all items with detailed info
            items_detail = []
            for key, entry in self._cache.items():
                age = entry.age
                last_access = (datetime.now() - entry.last_accessed).total_seconds()
                items_detail.append(
                    f"'{key}': value={type(entry.value).__name__}, "
                    f"age={age:.1f}s, last_access={last_access:.1f}s ago, "
                    f"accesses={entry.access_count}, ttl={entry.ttl}s"
                )
            
            return (
                f"CacheManager(max_size={self.max_size}, "
                f"default_ttl={self.default_ttl}, "
                f"items={len(self._cache)}:\n"
                f"  " + "\n  ".join(items_detail)
            )

# Global cache manager instance - single cache for all data types
_cache_manager = CacheManager(max_size=200, default_ttl=Hours(6))


def get_cache_manager() -> CacheManager:
    """Get the single cache manager instance."""

    return _cache_manager


def cache_result(
        ttl: int = Hours(1),
        key_prefix: str = '',
    ) -> Callable[..., T]:
    """
    Decorator to cache function results.
    
    Cache keys are organized by object IDs:
    - Series: series:{series_id}:{function_name}:{args_hash}
    - Episode: episode:{episode_id}:series:{series_id}:{function_name}:{args_hash}
    - Card: card:{card_id}:episode:{episode_id}:series:{series_id}:{function_name}:{args_hash}

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys (e.g., 'series', 'episode', 'card')
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache_manager = get_cache_manager()

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key with object ID hierarchy
            cache_key = _generate_hierarchical_key(func.__name__, args, kwargs, key_prefix)
            
            # Try to get from cache
            if (cached_result := cache_manager.get(cache_key)) is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator


def _generate_hierarchical_key(func_name: str, args: tuple, kwargs: dict, key_prefix: str) -> str:
    """
    Generate a hierarchical cache key based on object IDs.
    
    Args:
        func_name: Name of the function being cached
        args: Function arguments
        kwargs: Function keyword arguments
        key_prefix: Prefix indicating the data type (series, episode, card)
        
    Returns:
        Hierarchical cache key string
    """
    
    # Extract object IDs from arguments
    series_id = None
    episode_id = None
    card_id = None
    
    # Look for ID parameters in args and kwargs
    for arg in args:
        if isinstance(arg, int) and arg > 0:
            if series_id is None:
                series_id = arg
            elif episode_id is None:
                episode_id = arg
            elif card_id is None:
                card_id = arg
    
    # Also check kwargs for explicit ID parameters
    if 'series_id' in kwargs:
        series_id = kwargs['series_id']
    if 'episode_id' in kwargs:
        episode_id = kwargs['episode_id']
    if 'card_id' in kwargs:
        card_id = kwargs['card_id']
    
    # Generate hierarchical key
    if key_prefix == 'card' and card_id and episode_id and series_id:
        return f'card:{card_id}:episode:{episode_id}:series:{series_id}:{func_name}'
    elif key_prefix == 'episode' and episode_id and series_id:
        return f'episode:{episode_id}:series:{series_id}:{func_name}'
    elif key_prefix == 'series' and series_id:
        return f'series:{series_id}:{func_name}'
    else:
        # Fallback to function-based key if no clear hierarchy
        args_hash = _cache_manager._generate_key(args, kwargs)
        return f'{key_prefix}:{func_name}:{args_hash}'


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.

    Args:
        pattern: Pattern to match

    Returns:
        Number of entries invalidated
    """

    return get_cache_manager().invalidate_pattern(pattern)


def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Cache statistics dictionary
    """

    return get_cache_manager().get_stats()


def clear_all_caches() -> int:
    """Clear all cache entries and return count of cleared entries."""

    return get_cache_manager().clear()


def invalidate_series_cache(series_id: int) -> int:
    """
    Invalidate all cache entries related to a specific series.
    
    This invalidates all cache entries containing the series_id, including:
    - Series-specific data
    - Episode data for this series
    - Card data for episodes in this series
    
    Args:
        series_id: Series ID
        
    Returns:
        Number of entries invalidated.
    """

    cache_manager = get_cache_manager()
    
    # Invalidate all cache entries containing this series_id
    pattern = f'*series:{series_id}*'
    return cache_manager.invalidate_pattern(pattern)


def invalidate_episode_cache(episode_id: int) -> int:
    """
    Invalidate all cache entries related to a specific episode.
    
    This invalidates all cache entries containing the episode_id, including:
    - Episode-specific data
    - Card data for this episode
    
    Args:
        episode_id: Episode ID
        
    Returns:
        Number of entries invalidated.
    """

    cache_manager = get_cache_manager()
    
    # Invalidate all cache entries containing this episode_id
    pattern = f'*episode:{episode_id}*'
    return cache_manager.invalidate_pattern(pattern)


def invalidate_card_cache(card: 'Card') -> int:
    """
    Invalidate all cache entries related to a specific card.
    
    This invalidates all cache entries containing the card_id, and also
    invalidates related episode and series caches since cards are related
    to both episodes and series.

    Args:
        card: Card object to invalidate cache for

    Returns:
        Number of entries invalidated.
    """

    cache_manager = get_cache_manager()
    total_invalidated = 0
    
    # Invalidate card-specific cache entries
    if hasattr(card, 'id') and card.id:
        pattern = f'*card:{card.id}*'
        total_invalidated += cache_manager.invalidate_pattern(pattern)

    # Invalidate episode cache since cards are related to episodes
    if hasattr(card, 'episode_id') and card.episode_id:
        pattern = f'*episode:{card.episode_id}*'
        total_invalidated += cache_manager.invalidate_pattern(pattern)

    # Invalidate series cache since cards are related to series
    if hasattr(card, 'series_id') and card.series_id:
        pattern = f'*series:{card.series_id}*'
        total_invalidated += cache_manager.invalidate_pattern(pattern)

    log.debug(f'Invalidated {total_invalidated} card cache entries')
    return total_invalidated


def invalidate_all_card_cache() -> int:
    """
    Invalidate all card cache entries.
    
    Returns:
        Number of entries invalidated.
    """
    
    cache_manager = get_cache_manager()
    return cache_manager.invalidate_pattern('*card:*')


def invalidate_card_cache_pattern(pattern: str) -> int:
    """
    Invalidate card cache entries matching a pattern.

    Args:
        pattern: Pattern to match (supports wildcards)

    Returns:
        Number of entries invalidated.
    """
    
    cache_manager = get_cache_manager()
    return cache_manager.invalidate_pattern(f'*card:*{pattern}*')
