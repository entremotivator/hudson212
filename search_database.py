import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import Client
import streamlit as st

def get_supabase_client() -> Client:
    """Get Supabase client from session state"""
    return st.session_state.get("supabase")

def save_property_search(user_id: str, property_data: Dict[str, Any], search_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Save property search data to database"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return {"success": False, "message": "Database connection not available"}
        
        search_record = {
            "user_id": user_id,
            "property_data": property_data,
            "search_params": search_params or {},
            "search_date": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        response = supabase.table("property_searches").insert(search_record).execute()
        
        if response.data:
            return {"success": True, "search_id": response.data[0]["id"]}
        else:
            return {"success": False, "message": "Failed to save search"}
            
    except Exception as e:
        # Fallback to local storage for demo
        return save_search_locally(user_id, property_data, search_params)

def save_search_locally(user_id: str, property_data: Dict[str, Any], search_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Save search data locally for demo purposes"""
    try:
        # Create local storage directory
        storage_dir = "/home/ubuntu/property_app/local_storage"
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing searches
        searches_file = os.path.join(storage_dir, f"searches_{user_id}.json")
        searches = []
        if os.path.exists(searches_file):
            with open(searches_file, 'r') as f:
                searches = json.load(f)
        
        # Add new search
        search_id = f"search_{len(searches) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        search_record = {
            "id": search_id,
            "user_id": user_id,
            "property_data": property_data,
            "search_params": search_params or {},
            "search_date": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        searches.append(search_record)
        
        # Save back to file
        with open(searches_file, 'w') as f:
            json.dump(searches, f, indent=2)
        
        return {"success": True, "search_id": search_id}
        
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_user_searches(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get user's property searches"""
    try:
        supabase = get_supabase_client()
        if supabase:
            response = supabase.table("property_searches").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            return response.data if response.data else []
        else:
            # Fallback to local storage
            return get_searches_locally(user_id, limit)
            
    except Exception as e:
        # Fallback to local storage
        return get_searches_locally(user_id, limit)

def get_searches_locally(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get searches from local storage"""
    try:
        storage_dir = "/home/ubuntu/property_app/local_storage"
        searches_file = os.path.join(storage_dir, f"searches_{user_id}.json")
        
        if os.path.exists(searches_file):
            with open(searches_file, 'r') as f:
                searches = json.load(f)
            
            # Sort by created_at descending and limit
            searches.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return searches[:limit]
        else:
            return []
            
    except Exception as e:
        return []

def get_search_by_id(search_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Get specific search by ID"""
    try:
        supabase = get_supabase_client()
        if supabase:
            response = supabase.table("property_searches").select("*").eq("id", search_id).eq("user_id", user_id).execute()
            return response.data[0] if response.data else None
        else:
            # Fallback to local storage
            searches = get_searches_locally(user_id, 1000)
            for search in searches:
                if search.get("id") == search_id:
                    return search
            return None
            
    except Exception as e:
        return None

def delete_search(search_id: str, user_id: str) -> Dict[str, Any]:
    """Delete a search"""
    try:
        supabase = get_supabase_client()
        if supabase:
            response = supabase.table("property_searches").delete().eq("id", search_id).eq("user_id", user_id).execute()
            return {"success": True}
        else:
            # Fallback to local storage
            return delete_search_locally(search_id, user_id)
            
    except Exception as e:
        return {"success": False, "message": str(e)}

def delete_search_locally(search_id: str, user_id: str) -> Dict[str, Any]:
    """Delete search from local storage"""
    try:
        storage_dir = "/home/ubuntu/property_app/local_storage"
        searches_file = os.path.join(storage_dir, f"searches_{user_id}.json")
        
        if os.path.exists(searches_file):
            with open(searches_file, 'r') as f:
                searches = json.load(f)
            
            # Remove the search
            searches = [s for s in searches if s.get("id") != search_id]
            
            # Save back to file
            with open(searches_file, 'w') as f:
                json.dump(searches, f, indent=2)
            
            return {"success": True}
        else:
            return {"success": False, "message": "Search not found"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_search_statistics(user_id: str) -> Dict[str, Any]:
    """Get search statistics for user"""
    try:
        searches = get_user_searches(user_id, 1000)
        saved_searches = get_saved_searches(user_id)
        
        return {
            "total_searches": len(searches),
            "saved_searches": len(saved_searches),
            "total_properties": sum(len(s.get("property_data", {}).get("results", [])) for s in searches)
        }
        
    except Exception as e:
        return {"total_searches": 0, "saved_searches": 0, "total_properties": 0}

def save_named_search(user_id: str, search_name: str, search_criteria: Dict[str, Any], auto_notify: bool = False) -> Dict[str, Any]:
    """Save a named search with criteria"""
    try:
        supabase = get_supabase_client()
        if supabase:
            search_record = {
                "user_id": user_id,
                "search_name": search_name,
                "search_criteria": search_criteria,
                "auto_notify": auto_notify,
                "created_at": datetime.now().isoformat(),
                "results_count": 0
            }
            
            response = supabase.table("saved_searches").insert(search_record).execute()
            return {"success": True}
        else:
            # Fallback to local storage
            return save_named_search_locally(user_id, search_name, search_criteria, auto_notify)
            
    except Exception as e:
        return {"success": False, "message": str(e)}

def save_named_search_locally(user_id: str, search_name: str, search_criteria: Dict[str, Any], auto_notify: bool = False) -> Dict[str, Any]:
    """Save named search locally"""
    try:
        storage_dir = "/home/ubuntu/property_app/local_storage"
        os.makedirs(storage_dir, exist_ok=True)
        
        saved_file = os.path.join(storage_dir, f"saved_searches_{user_id}.json")
        saved_searches = []
        if os.path.exists(saved_file):
            with open(saved_file, 'r') as f:
                saved_searches = json.load(f)
        
        search_record = {
            "id": f"saved_{len(saved_searches) + 1}",
            "user_id": user_id,
            "search_name": search_name,
            "search_criteria": search_criteria,
            "auto_notify": auto_notify,
            "created_at": datetime.now().isoformat(),
            "results_count": 0
        }
        
        saved_searches.append(search_record)
        
        with open(saved_file, 'w') as f:
            json.dump(saved_searches, f, indent=2)
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_saved_searches(user_id: str) -> List[Dict[str, Any]]:
    """Get user's saved searches"""
    try:
        supabase = get_supabase_client()
        if supabase:
            response = supabase.table("saved_searches").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return response.data if response.data else []
        else:
            # Fallback to local storage
            return get_saved_searches_locally(user_id)
            
    except Exception as e:
        return get_saved_searches_locally(user_id)

def get_saved_searches_locally(user_id: str) -> List[Dict[str, Any]]:
    """Get saved searches from local storage"""
    try:
        storage_dir = "/home/ubuntu/property_app/local_storage"
        saved_file = os.path.join(storage_dir, f"saved_searches_{user_id}.json")
        
        if os.path.exists(saved_file):
            with open(saved_file, 'r') as f:
                return json.load(f)
        else:
            return []
            
    except Exception as e:
        return []

# Initialize with sample data for demo
def initialize_demo_data():
    """Initialize demo data for testing"""
    demo_user_id = "demo-user-123"
    
    # Sample property data from the uploaded JSON
    sample_property_data = {
        "address": "2397 dawn drive, Decatur, GA 30032",
        "results": [
            {
                "id": "2397-Dawn-Dr,-Decatur,-GA-30032",
                "city": "Decatur",
                "owner": {
                    "type": "Individual",
                    "names": ["Yvonne H Beiser"],
                    "mailingAddress": {
                        "id": "2397-Dawn-Dr,-Decatur,-GA-30032",
                        "city": "Decatur",
                        "state": "GA",
                        "zipCode": "30032",
                        "stateFips": "13",
                        "addressLine1": "2397 Dawn Dr",
                        "addressLine2": None,
                        "formattedAddress": "2397 Dawn Dr, Decatur, GA 30032"
                    }
                },
                "state": "GA",
                "county": "Dekalb",
                "zoning": "R75",
                "history": {
                    "1997-01-22": {
                        "date": "1997-01-22T00:00:00.000Z",
                        "event": "Sale",
                        "price": 76000
                    }
                },
                "lotSize": 18731,
                "zipCode": "30032",
                "bedrooms": 3,
                "features": {
                    "garage": True,
                    "cooling": True,
                    "heating": True,
                    "roofType": "Asphalt",
                    "fireplace": True,
                    "roomCount": 8,
                    "unitCount": 1,
                    "floorCount": 2,
                    "garageType": "Carport",
                    "coolingType": "Central",
                    "heatingType": "Central",
                    "exteriorType": "Brick",
                    "garageSpaces": 2,
                    "fireplaceType": "Masonry",
                    "foundationType": "Concrete",
                    "architectureType": "Split Level"
                },
                "latitude": 33.719303,
                "bathrooms": 2,
                "longitude": -84.294256,
                "stateFips": "13",
                "yearBuilt": 1960,
                "assessorID": "15 139 01 009",
                "countyFips": "089",
                "subdivision": "HIGHLAND PARK",
                "addressLine1": "2397 Dawn Dr",
                "addressLine2": None,
                "lastSaleDate": "1997-01-22T00:00:00.000Z",
                "propertyType": "Single Family",
                "lastSalePrice": 76000,
                "ownerOccupied": True,
                "propertyTaxes": {
                    "2019": {"year": 2019, "total": 2221},
                    "2022": {"year": 2022, "total": 3597},
                    "2023": {"year": 2023, "total": 4420},
                    "2024": {"year": 2024, "total": 4723}
                },
                "squareFootage": 2004,
                "taxAssessments": {
                    "2019": {"land": 15200, "year": 2019, "value": 42760, "improvements": 27560},
                    "2022": {"land": 15200, "year": 2022, "value": 74120, "improvements": 58920},
                    "2023": {"land": 29320, "year": 2023, "value": 92000, "improvements": 62680},
                    "2024": {"land": 29320, "year": 2024, "value": 97720, "improvements": 68400}
                },
                "formattedAddress": "2397 Dawn Dr, Decatur, GA 30032",
                "legalDescription": "CITY/MUNI/TWP:UNINCORPORATED"
            }
        ],
        "search_params": {"address": "2397 dawn drive, Decatur, GA 30032"},
        "search_timestamp": "2025-08-28T03:19:46.214775"
    }
    
    # Save sample search
    save_search_locally(demo_user_id, sample_property_data, {"address": "2397 dawn drive, Decatur, GA 30032"})
    
    # Save sample named search
    save_named_search_locally(
        demo_user_id,
        "Decatur Single Family Homes",
        {
            "address": "Decatur, GA",
            "min_bedrooms": 3,
            "min_bathrooms": 2,
            "max_price": 200000,
            "property_type": "Single Family"
        },
        auto_notify=True
    )

