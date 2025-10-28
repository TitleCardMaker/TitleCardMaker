from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.users import get_current_user
from app.dependencies import get_logger
from app.logging.logger import Logger
from app.core.cache import (
    clear_all_caches,
    get_cache_manager,
    get_cache_stats,
    invalidate_cache_pattern,
)

# Create sub router for all /cache API requests
cache_router = APIRouter(
    prefix='/cache',
    tags=['Cache Management'],
    dependencies=[Depends(get_current_user)],
)


@cache_router.get('/stats')
def get_cache_statistics(
    log: Logger = Depends(get_logger),
) -> dict:
    """
    Get cache statistics for monitoring performance.
    """
    
    try:
        stats = get_cache_stats()
        log.debug(f"Retrieved cache statistics")
        return stats
    except Exception as e:
        log.error(f"Error retrieving cache statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cache statistics: {str(e)}"
        )


@cache_router.delete('/clear')
def clear_cache_endpoint(
    cache_type: str | None = Query(default=None, description="Optional specific cache type to clear"),
    log: Logger = Depends(get_logger),
) -> dict:
    """
    Clear cache entries.
    
    - cache_type: Optional specific cache type to clear (series, card, episode, template)
    """
    
    try:
        if cache_type:
            # For backward compatibility, we'll clear cache entries matching the type pattern
            cache_manager = get_cache_manager()
            cleared_count = cache_manager.invalidate_pattern(f'*{cache_type}:*')
            log.info(f"Cleared {cleared_count} entries from {cache_type} cache")
            return {
                "message": f"Cleared {cleared_count} entries from {cache_type} cache",
                "cleared_count": cleared_count,
                "cache_type": cache_type
            }
        else:
            cleared_count = clear_all_caches()
            log.info(f"Cleared all caches: {cleared_count} total entries")
            return {
                "message": f"Cleared {cleared_count} total entries from all caches",
                "cleared_count": cleared_count
            }
    except Exception as e:
        log.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@cache_router.delete('/invalidate')
def invalidate_cache_pattern_endpoint(
    pattern: str = Query(..., description="Pattern to match for invalidation"),
    log: Logger = Depends(get_logger),
) -> dict:
    """
    Invalidate cache entries matching a pattern.
    
    - pattern: Pattern to match (supports wildcards)
    """
    
    try:
        invalidated_count = invalidate_cache_pattern(pattern)
        log.info(f"Invalidated {invalidated_count} entries matching pattern '{pattern}'")
        return {
            "message": f"Invalidated {invalidated_count} entries matching pattern '{pattern}'",
            "invalidated_count": invalidated_count,
            "pattern": pattern
        }
    except Exception as e:
        log.error(f"Error invalidating cache pattern: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache pattern: {str(e)}"
        )


@cache_router.get('/health')
def cache_health_check(
    log: Logger = Depends(get_logger),
) -> dict:
    """
    Check cache health and performance metrics.
    """
    
    try:
        stats = get_cache_stats()
        
        # Calculate overall health metrics
        total_hits = stats['hits']
        total_misses = stats['misses']
        total_requests = total_hits + total_misses
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0.0
        
        # Check for potential issues
        issues = []
        if stats['size'] >= stats['max_size'] * 0.9:
            issues.append(f"Cache nearly full ({stats['size']}/{stats['max_size']})")
        
        if stats['errors'] > 0:
            issues.append(f"{stats['errors']} errors detected")
        
        health_status = "healthy" if not issues else "warning"
        
        return {
            "status": health_status,
            "overall_hit_rate": overall_hit_rate,
            "total_requests": total_requests,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "issues": issues,
            "cache_stats": stats
        }
    except Exception as e:
        log.error(f"Error checking cache health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check cache health: {str(e)}"
        ) 