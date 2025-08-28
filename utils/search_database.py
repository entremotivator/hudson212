import streamlit as st
import json
from datetime import datetime
from utils.auth import get_user_client


def save_property_search(user_id, address, search_results, search_params=None):
    """
    Save a property search to Supabase property_searches table.
    
    Args:
        user_id: User ID (UUID)
        address: The searched address
        search_results: The API response data
        search_params: Optional search parameters
    
    Returns:
        dict: Success status and search ID
    """
    client = get_user_client()
    if not client:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        # Prepare the data to save
        search_data = {
            "user_id": str(user_id),
            "property_data": {
                "address": address,
                "results": search_results,
                "search_params": search_params or {},
                "search_timestamp": datetime.now().isoformat()
            }
        }
        
        # Insert into property_searches table
        response = client.table("property_searches").insert(search_data).execute()
        
        if response.data:
            return {
                "success": True, 
                "search_id": response.data[0]["id"],
                "message": "Search saved successfully"
            }
        else:
            return {"success": False, "message": "Failed to save search"}
            
    except Exception as e:
        return {"success": False, "message": f"Error saving search: {str(e)}"}


def get_user_searches(user_id, limit=50, offset=0):
    """
    Retrieve user's saved searches from Supabase.
    
    Args:
        user_id: User ID (UUID)
        limit: Maximum number of searches to return
        offset: Number of searches to skip (for pagination)
    
    Returns:
        list: List of saved searches
    """
    client = get_user_client()
    if not client:
        return []
    
    try:
        response = client.table("property_searches")\
            .select("*")\
            .eq("user_id", str(user_id))\
            .order("search_date", desc=True)\
            .limit(limit)\
            .offset(offset)\
            .execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"Error retrieving searches: {str(e)}")
        return []


def get_search_by_id(search_id, user_id):
    """
    Get a specific search by ID (with user verification).
    
    Args:
        search_id: Search ID
        user_id: User ID for verification
    
    Returns:
        dict: Search data or None
    """
    client = get_user_client()
    if not client:
        return None
    
    try:
        response = client.table("property_searches")\
            .select("*")\
            .eq("id", search_id)\
            .eq("user_id", str(user_id))\
            .execute()
        
        return response.data[0] if response.data else None
        
    except Exception as e:
        st.error(f"Error retrieving search: {str(e)}")
        return None


def delete_search(search_id, user_id):
    """
    Delete a search (with user verification).
    
    Args:
        search_id: Search ID
        user_id: User ID for verification
    
    Returns:
        dict: Success status
    """
    client = get_user_client()
    if not client:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        response = client.table("property_searches")\
            .delete()\
            .eq("id", search_id)\
            .eq("user_id", str(user_id))\
            .execute()
        
        return {"success": True, "message": "Search deleted successfully"}
        
    except Exception as e:
        return {"success": False, "message": f"Error deleting search: {str(e)}"}


def save_named_search(user_id, search_name, search_criteria, auto_notify=False):
    """
    Save a named search to the saved_searches table for future reuse.
    
    Args:
        user_id: User ID (bigint)
        search_name: Name for the saved search
        search_criteria: Search criteria as JSON
        auto_notify: Whether to auto-notify on new results
    
    Returns:
        dict: Success status and saved search ID
    """
    client = get_user_client()
    if not client:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        search_data = {
            "user_id": int(user_id),  # saved_searches uses bigint
            "search_name": search_name,
            "search_criteria": search_criteria,
            "auto_notify": auto_notify,
            "results_count": 0
        }
        
        response = client.table("saved_searches").insert(search_data).execute()
        
        if response.data:
            return {
                "success": True,
                "saved_search_id": response.data[0]["id"],
                "message": "Named search saved successfully"
            }
        else:
            return {"success": False, "message": "Failed to save named search"}
            
    except Exception as e:
        return {"success": False, "message": f"Error saving named search: {str(e)}"}


def get_saved_searches(user_id):
    """
    Get user's saved/named searches.
    
    Args:
        user_id: User ID (bigint)
    
    Returns:
        list: List of saved searches
    """
    client = get_user_client()
    if not client:
        return []
    
    try:
        response = client.table("saved_searches")\
            .select("*")\
            .eq("user_id", int(user_id))\
            .order("created_at", desc=True)\
            .execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"Error retrieving saved searches: {str(e)}")
        return []


def update_saved_search_results(saved_search_id, results_count):
    """
    Update the results count for a saved search.
    
    Args:
        saved_search_id: Saved search ID
        results_count: Number of results found
    
    Returns:
        dict: Success status
    """
    client = get_user_client()
    if not client:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        response = client.table("saved_searches")\
            .update({
                "results_count": results_count,
                "last_run": datetime.now().isoformat()
            })\
            .eq("id", saved_search_id)\
            .execute()
        
        return {"success": True, "message": "Search results updated"}
        
    except Exception as e:
        return {"success": False, "message": f"Error updating search: {str(e)}"}


def get_search_statistics(user_id):
    """
    Get search statistics for the user.
    
    Args:
        user_id: User ID
    
    Returns:
        dict: Search statistics
    """
    client = get_user_client()
    if not client:
        return {"total_searches": 0, "saved_searches": 0}
    
    try:
        # Get total property searches
        total_response = client.table("property_searches")\
            .select("id", count="exact")\
            .eq("user_id", str(user_id))\
            .execute()
        
        # Get saved searches count
        saved_response = client.table("saved_searches")\
            .select("id", count="exact")\
            .eq("user_id", int(user_id))\
            .execute()
        
        return {
            "total_searches": total_response.count or 0,
            "saved_searches": saved_response.count or 0
        }
        
    except Exception as e:
        st.error(f"Error getting statistics: {str(e)}")
        return {"total_searches": 0, "saved_searches": 0}

