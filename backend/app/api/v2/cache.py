"""
Cache management API endpoints for monitoring and controlling the caching system.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.users import get_current_user
from app.dependencies import get_database, get_logger
from app.logging.logger import Logger
from app.core.cache import (
    get_cache_stats,
    clear_all_caches,
    invalidate_cache_pattern,
    get_cache_manager
)

# Create sub router for all /cache API requests
cache_router = APIRouter(
    prefix='/cache',
    tags=['Cache Management'],
    dependencies=[Depends(get_current_user)],
)


@cache_router.get('/stats')
def get_cache_statistics(
    cache_type: str = Query(default=None, description="Specific cache type to get stats for"),
    db: Session = Depends(get_database),
    log: Logger = Depends(get_logger),
) -> dict:
    """
    Get cache statistics for monitoring performance.
    
    - cache_type: Optional specific cache type (series, card, episode, template)
    """
    
    try:
        stats = get_cache_stats(cache_type)
        log.debug(f"Retrieved cache statistics for {cache_type or 'all caches'}")
        return stats
    except Exception as e:
        log.error(f"Error retrieving cache statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cache statistics: {str(e)}"
        )


@cache_router.delete('/clear')
def clear_cache(
    cache_type: str = Query(default=None, description="Specific cache type to clear"),
    db: Session = Depends(get_database),
    log: Logger = Depends(get_logger),
) -> dict:
    """
    Clear cache entries.
    
    - cache_type: Optional specific cache type to clear (series, card, episode, template)
    """
    
    try:
        if cache_type:
            cache_manager = get_cache_manager(cache_type)
            cleared_count = cache_manager.clear()
            log.info(f"Cleared {cleared_count} entries from {cache_type} cache")
            return {
                "message": f"Cleared {cleared_count} entries from {cache_type} cache",
                "cleared_count": cleared_count,
                "cache_type": cache_type
            }
        else:
            cleared_counts = clear_all_caches()
            total_cleared = sum(cleared_counts.values())
            log.info(f"Cleared all caches: {cleared_counts}")
            return {
                "message": f"Cleared {total_cleared} total entries from all caches",
                "cleared_counts": cleared_counts,
                "total_cleared": total_cleared
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
    cache_type: str = Query(default='series', description="Cache type to invalidate"),
    db: Session = Depends(get_database),
    log: Logger = Depends(get_logger),
) -> dict:
    """
    Invalidate cache entries matching a pattern.
    
    - pattern: Pattern to match (supports wildcards)
    - cache_type: Cache type to invalidate
    """
    
    try:
        invalidated_count = invalidate_cache_pattern(pattern, cache_type)
        log.info(f"Invalidated {invalidated_count} entries matching pattern '{pattern}' in {cache_type} cache")
        return {
            "message": f"Invalidated {invalidated_count} entries matching pattern '{pattern}'",
            "invalidated_count": invalidated_count,
            "pattern": pattern,
            "cache_type": cache_type
        }
    except Exception as e:
        log.error(f"Error invalidating cache pattern: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache pattern: {str(e)}"
        )


@cache_router.get('/health')
def cache_health_check(
    db: Session = Depends(get_database),
    log: Logger = Depends(get_logger),
) -> dict:
    """
    Check cache health and performance metrics.
    """
    
    try:
        all_stats = get_cache_stats()
        
        # Calculate overall health metrics
        total_hits = sum(stats['hits'] for stats in all_stats.values())
        total_misses = sum(stats['misses'] for stats in all_stats.values())
        total_requests = total_hits + total_misses
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0.0
        
        # Check for potential issues
        issues = []
        for cache_type, stats in all_stats.items():
            if stats['size'] >= stats['max_size'] * 0.9:
                issues.append(f"{cache_type}: Cache nearly full ({stats['size']}/{stats['max_size']})")
            
            if stats['errors'] > 0:
                issues.append(f"{cache_type}: {stats['errors']} errors detected")
        
        health_status = "healthy" if not issues else "warning"
        
        return {
            "status": health_status,
            "overall_hit_rate": overall_hit_rate,
            "total_requests": total_requests,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "issues": issues,
            "cache_stats": all_stats
        }
    except Exception as e:
        log.error(f"Error checking cache health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check cache health: {str(e)}"
        ) 