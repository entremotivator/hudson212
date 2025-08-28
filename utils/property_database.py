# =====================================================
# utils/property_database.py (Supabase only)
# =====================================================

from supabase import create_client, Client
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os

logger = logging.getLogger(__name__)

class PropertySearchDatabase:
    """Database operations for property search history (Supabase REST only)"""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # use service role for insert/delete
        self.supabase: Client = create_client(url, key)

    def save_search(self, user_id: str, property_data: Dict[Any, Any], consumer_secret: str = None) -> bool:
        """Save property search to Supabase"""
        try:
            data = {
                "user_id": user_id,
                "property_data": property_data,
                "search_date": datetime.utcnow().isoformat(),
                "consumer_secret": consumer_secret
            }
            self.supabase.table("property_searches").insert(data).execute()
            logger.info(f"Property search saved for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving property search: {e}")
            return False
    
    def get_user_searches(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get user's property search history with pagination"""
        try:
            response = (
                self.supabase.table("property_searches")
                .select("id, property_data, search_date, consumer_secret")
                .eq("user_id", user_id)
                .order("search_date", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching property searches: {e}")
            return []
    
    def delete_search(self, search_id: int, user_id: str) -> bool:
        """Delete a specific property search"""
        try:
            response = (
                self.supabase.table("property_searches")
                .delete()
                .eq("id", search_id)
                .eq("user_id", user_id)
                .execute()
            )
            return response.count > 0
        except Exception as e:
            logger.error(f"Error deleting property search: {e}")
            return False
    
    def delete_all_user_searches(self, user_id: str) -> bool:
        """Delete all searches for a user"""
        try:
            self.supabase.table("property_searches").delete().eq("user_id", user_id).execute()
            logger.info(f"All searches deleted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting all user searches: {e}")
            return False
    
    def get_search_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get simple search statistics (Supabase can't run complex SQL easily)"""
        stats = {}
        try:
            # Total searches
            resp = self.supabase.table("property_searches").select("id", count="exact").eq("user_id", user_id).execute()
            stats["total_searches"] = resp.count or 0

            # Recent searches (last 30 days)
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            resp = (
                self.supabase.table("property_searches")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .gte("search_date", thirty_days_ago)
                .execute()
            )
            stats["recent_searches"] = resp.count or 0

            # Last 7 days
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            resp = (
                self.supabase.table("property_searches")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .gte("search_date", week_ago)
                .execute()
            )
            stats["week_searches"] = resp.count or 0

            return stats
        except Exception as e:
            logger.error(f"Error getting search statistics: {e}")
            return {}
    
    def export_user_searches(self, user_id: str, format: str = "json") -> Optional[str]:
        """Export all user searches"""
        try:
            response = (
                self.supabase.table("property_searches")
                .select("*")
                .eq("user_id", user_id)
                .limit(1000)
                .execute()
            )
            searches = response.data or []
            if format.lower() == "json":
                return json.dumps(searches, indent=2, default=str)
            return None
        except Exception as e:
            logger.error(f"Error exporting user searches: {e}")
            return None


# Convenience functions
def save_property_search(user_id: str, property_data: Dict[Any, Any], consumer_secret: str = None) -> bool:
    return PropertySearchDatabase().save_search(user_id, property_data, consumer_secret)

def get_user_property_searches(user_id: str, limit: int = 50) -> List[Dict]:
    return PropertySearchDatabase().get_user_searches(user_id, limit)

def delete_property_search(search_id: int, user_id: str) -> bool:
    return PropertySearchDatabase().delete_search(search_id, user_id)

def get_search_statistics(user_id: str) -> Dict[str, Any]:
    return PropertySearchDatabase().get_search_statistics(user_id)
