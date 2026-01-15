"""
MongoDB Counter Utility for Incremental IDs
"""
from loguru import logger
from app.models.database import get_database


async def get_next_bet_number() -> int:
    """
    Get next incremental bet number using MongoDB counter pattern
    
    Returns:
        Next bet number (1, 2, 3, ...)
    """
    db = get_database()
    counters_col = db["counters"]
    
    try:
        # Use findOneAndUpdate for atomic increment
        # This atomically increments and returns the NEW value
        result = await counters_col.find_one_and_update(
            {"_id": "bet_number"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        
        if result and "seq" in result:
            return result["seq"]
        else:
            # Should not happen, but fallback
            return 1
    except Exception as e:
        logger.error(f"Error getting next bet number: {e}")
        # Fallback: try to get current max bet number from bets collection
        try:
            bets_col = db["bets"]
            max_bet = await bets_col.find_one(
                {"bet_number": {"$exists": True}},
                sort=[("bet_number", -1)]
            )
            if max_bet and "bet_number" in max_bet:
                next_number = max_bet["bet_number"] + 1
                # Initialize counter with this value
                await counters_col.update_one(
                    {"_id": "bet_number"},
                    {"$set": {"seq": next_number}},
                    upsert=True
                )
                return next_number
        except Exception as fallback_error:
            logger.error(f"Fallback counter initialization failed: {fallback_error}")
        # Last resort: return 1
        return 1
