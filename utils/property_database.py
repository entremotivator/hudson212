# =====================================================
# utils/property_database.py
# =====================================================

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os

logger = logging.getLogger(__name__)

class PropertySearchDatabase:
    """Database operations for property search history"""
    
    def __init__(self):
        self.connection_params = {
            'host': os.getenv("SUPABASE_DB_HOST"),
            'database': os.getenv("SUPABASE_DB_NAME"),
            'user': os.getenv("SUPABASE_DB_USER"),
            'password': os.getenv("SUPABASE_DB_PASSWORD"),
            'port': os.getenv("SUPABASE_DB_PORT", "5432")
        }
    
    def get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.connection_params)
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def save_search(self, user_id: str, property_data: Dict[Any, Any], consumer_secret: str = None) -> bool:
        """Save property search to database"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
                
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO property_searches (user_id, property_data, search_date, consumer_secret)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, json.dumps(property_data, default=str), datetime.now(), consumer_secret))
                conn.commit()
            
            conn.close()
            logger.info(f"Property search saved for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving property search: {e}")
            return False
    
    def get_user_searches(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get user's property search history with pagination"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
                
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, property_data, search_date, consumer_secret
                    FROM property_searches 
                    WHERE user_id = %s 
                    ORDER BY search_date DESC 
                    LIMIT %s OFFSET %s
                """, (user_id, limit, offset))
                results = cur.fetchall()
            
            conn.close()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching property searches: {e}")
            return []
    
    def get_searches_by_date_range(self, user_id: str, start_date: datetime, end_date: datetime = None) -> List[Dict]:
        """Get searches within a date range"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            end_date = end_date or datetime.now()
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, property_data, search_date, consumer_secret
                    FROM property_searches 
                    WHERE user_id = %s AND search_date BETWEEN %s AND %s
                    ORDER BY search_date DESC
                """, (user_id, start_date, end_date))
                results = cur.fetchall()
            
            conn.close()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching searches by date range: {e}")
            return []
    
    def search_properties(self, user_id: str, search_term: str) -> List[Dict]:
        """Search properties by address or other criteria"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
                
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Use PostgreSQL's JSONB search capabilities
                cur.execute("""
                    SELECT id, property_data, search_date, consumer_secret
                    FROM property_searches 
                    WHERE user_id = %s 
                    AND (
                        property_data->>'formattedAddress' ILIKE %s 
                        OR property_data->>'address' ILIKE %s
                        OR property_data->>'city' ILIKE %s
                        OR property_data->>'state' ILIKE %s
                        OR property_data->>'zipCode' ILIKE %s
                    )
                    ORDER BY search_date DESC
                """, (user_id, f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                results = cur.fetchall()
            
            conn.close()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error searching properties: {e}")
            return []
    
    def delete_search(self, search_id: int, user_id: str) -> bool:
        """Delete a specific property search"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
                
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM property_searches 
                    WHERE id = %s AND user_id = %s
                """, (search_id, user_id))
                rows_affected = cur.rowcount
                conn.commit()
            
            conn.close()
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting property search: {e}")
            return False
    
    def delete_all_user_searches(self, user_id: str) -> bool:
        """Delete all searches for a user"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
                
            with conn.cursor() as cur:
                cur.execute("DELETE FROM property_searches WHERE user_id = %s", (user_id,))
                conn.commit()
            
            conn.close()
            logger.info(f"All searches deleted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting all user searches: {e}")
            return False
    
    def get_search_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive search statistics for a user"""
        try:
            conn = self.get_connection()
            if not conn:
                return {}
                
            stats = {}
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Total searches
                cur.execute("SELECT COUNT(*) as total FROM property_searches WHERE user_id = %s", (user_id,))
                stats['total_searches'] = cur.fetchone()['total']
                
                # Recent searches (last 30 days)
                cur.execute("""
                    SELECT COUNT(*) as recent 
                    FROM property_searches 
                    WHERE user_id = %s AND search_date >= %s
                """, (user_id, datetime.now() - timedelta(days=30)))
                stats['recent_searches'] = cur.fetchone()['recent']
                
                # Searches this week
                cur.execute("""
                    SELECT COUNT(*) as week 
                    FROM property_searches 
                    WHERE user_id = %s AND search_date >= %s
                """, (user_id, datetime.now() - timedelta(days=7)))
                stats['week_searches'] = cur.fetchone()['week']
                
                # Most searched property types
                cur.execute("""
                    SELECT 
                        property_data->>'propertyType' as property_type,
                        COUNT(*) as count
                    FROM property_searches 
                    WHERE user_id = %s 
                        AND property_data->>'propertyType' IS NOT NULL
                        AND property_data->>'propertyType' != 'N/A'
                    GROUP BY property_data->>'propertyType'
                    ORDER BY count DESC
                    LIMIT 5
                """, (user_id,))
                stats['top_property_types'] = [dict(row) for row in cur.fetchall()]
                
                # Most searched cities
                cur.execute("""
                    SELECT 
                        COALESCE(property_data->>'city', 'Unknown') as city,
                        COUNT(*) as count
                    FROM property_searches 
                    WHERE user_id = %s 
                        AND property_data->>'city' IS NOT NULL
                        AND property_data->>'city' != 'N/A'
                    GROUP BY property_data->>'city'
                    ORDER BY count DESC
                    LIMIT 5
                """, (user_id,))
                stats['top_cities'] = [dict(row) for row in cur.fetchall()]
                
                # Average property value (where available)
                try:
                    cur.execute("""
                        SELECT 
                            AVG((property_data->>'estimatedValue')::numeric) as avg_value,
                            MIN((property_data->>'estimatedValue')::numeric) as min_value,
                            MAX((property_data->>'estimatedValue')::numeric) as max_value
                        FROM property_searches 
                        WHERE user_id = %s 
                            AND property_data->>'estimatedValue' IS NOT NULL
                            AND property_data->>'estimatedValue' != 'N/A'
                            AND property_data->>'estimatedValue' != ''
                            AND (property_data->>'estimatedValue')::text ~ '^[0-9]+(\.[0-9]+)?$'
                            AND LENGTH(property_data->>'estimatedValue') < 20
                            AND property_data->>'estimatedValue' NOT LIKE '%-%'
                    """, (user_id,))
                    value_stats = cur.fetchone()
                    if value_stats and value_stats['avg_value']:
                        stats['value_statistics'] = {
                            'average': float(value_stats['avg_value']),
                            'minimum': float(value_stats['min_value']),
                            'maximum': float(value_stats['max_value'])
                        }
                except Exception as value_error:
                    logger.warning(f"Could not calculate value statistics for user {user_id}: {value_error}")
                    # Continue without value statistics
                
                # Search frequency over time (last 12 months)
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('month', search_date) as month,
                        COUNT(*) as count
                    FROM property_searches 
                    WHERE user_id = %s 
                        AND search_date >= %s
                    GROUP BY DATE_TRUNC('month', search_date)
                    ORDER BY month DESC
                """, (user_id, datetime.now() - timedelta(days=365)))
                stats['monthly_activity'] = [dict(row) for row in cur.fetchall()]
            
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"Error getting search statistics: {e}")
            return {}
    
    def get_duplicate_searches(self, user_id: str) -> List[Dict]:
        """Find duplicate searches (same property searched multiple times)"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
                
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        property_data->>'formattedAddress' as address,
                        COUNT(*) as search_count,
                        MIN(search_date) as first_search,
                        MAX(search_date) as last_search,
                        ARRAY_AGG(id ORDER BY search_date DESC) as search_ids
                    FROM property_searches 
                    WHERE user_id = %s 
                        AND property_data->>'formattedAddress' IS NOT NULL
                    GROUP BY property_data->>'formattedAddress'
                    HAVING COUNT(*) > 1
                    ORDER BY search_count DESC, last_search DESC
                """, (user_id,))
                results = cur.fetchall()
            
            conn.close()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error finding duplicate searches: {e}")
            return []
    
    def cleanup_old_searches(self, user_id: str, days_to_keep: int = 365) -> int:
        """Clean up searches older than specified days"""
        try:
            conn = self.get_connection()
            if not conn:
                return 0
                
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM property_searches 
                    WHERE user_id = %s AND search_date < %s
                """, (user_id, cutoff_date))
                deleted_count = cur.rowcount
                conn.commit()
            
            conn.close()
            logger.info(f"Cleaned up {deleted_count} old searches for user {user_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old searches: {e}")
            return 0
    
    def export_user_searches(self, user_id: str, format: str = 'json') -> Optional[str]:
        """Export all user searches in specified format"""
        try:
            searches = self.get_user_searches(user_id, limit=1000)  # Get all searches
            
            if format.lower() == 'json':
                # Convert datetime objects to strings for JSON serialization
                for search in searches:
                    if 'search_date' in search:
                        search['search_date'] = search['search_date'].isoformat()
                
                return json.dumps(searches, indent=2, default=str)
            
            # Could add CSV, XML formats here
            return None
            
        except Exception as e:
            logger.error(f"Error exporting user searches: {e}")
            return None

# Convenience functions for backwards compatibility
def save_property_search(user_id: str, property_data: Dict[Any, Any], consumer_secret: str = None) -> bool:
    """Convenience function for saving searches"""
    db = PropertySearchDatabase()
    return db.save_search(user_id, property_data, consumer_secret)

def get_user_property_searches(user_id: str, limit: int = 50) -> List[Dict]:
    """Convenience function for getting user searches"""
    db = PropertySearchDatabase()
    return db.get_user_searches(user_id, limit)

def delete_property_search(search_id: int, user_id: str) -> bool:
    """Convenience function for deleting searches"""
    db = PropertySearchDatabase()
    return db.delete_search(search_id, user_id)

def get_search_statistics(user_id: str) -> Dict[str, Any]:
    """Convenience function for getting statistics"""
    db = PropertySearchDatabase()
    return db.get_search_statistics(user_id)
