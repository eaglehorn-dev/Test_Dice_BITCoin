"""
Fairness API routes - Public server seed transparency
"""
from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from loguru import logger

from app.services.server_seed_service import ServerSeedService

router = APIRouter(prefix="/api/fairness", tags=["fairness"])


@router.get("/seeds")
async def get_fairness_seeds():
    """
    Get server seeds for fairness transparency page
    Shows seeds from past dates up to 3 days in the future
    Real keys only shown for past dates (not today or future)
    
    Returns:
        List of server seeds with real keys for past dates only
    """
    try:
        seed_service = ServerSeedService()
        all_seeds = await seed_service.get_all_seeds()
        
        today = date.today()
        three_days_later = today + timedelta(days=3)
        
        # Filter seeds: from past dates up to 3 days in the future
        filtered_seeds = []
        for seed in all_seeds:
            seed_date_str = seed.get("seed_date")
            if not seed_date_str:
                continue
            
            try:
                seed_date = date.fromisoformat(seed_date_str)
                # Only include seeds from past up to 3 days in future
                if seed_date <= three_days_later:
                    # Only show real key for past dates (not today or future)
                    is_past = seed_date < today
                    
                    seed_info = {
                        "seed_id": str(seed["_id"]),
                        "seed_date": seed_date_str,
                        "server_seed_hash": seed["server_seed_hash"],
                        "server_seed": seed.get("server_seed") if is_past else None,  # Only past dates
                        "bet_count": seed.get("bet_count", 0),
                        "created_at": seed.get("created_at")
                    }
                    filtered_seeds.append(seed_info)
            except (ValueError, TypeError):
                continue
        
        # Also ensure today's seed exists (auto-generate if needed)
        today_str = today.isoformat()
        today_seed_exists = any(s["seed_date"] == today_str for s in filtered_seeds)
        if not today_seed_exists:
            # Auto-generate today's seed
            today_seed = await seed_service.get_today_server_seed()
            if today_seed:
                filtered_seeds.append({
                    "seed_id": str(today_seed["_id"]),
                    "seed_date": today_seed["seed_date"],
                    "server_seed_hash": today_seed["server_seed_hash"],
                    "server_seed": None,  # Today's key not published
                    "bet_count": today_seed.get("bet_count", 0),
                    "created_at": today_seed.get("created_at")
                })
        
        # Sort by date (newest first)
        filtered_seeds.sort(key=lambda x: x["seed_date"], reverse=True)
        
        return {
            "seeds": filtered_seeds,
            "today": today.isoformat(),
            "three_days_later": three_days_later.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting fairness seeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))
