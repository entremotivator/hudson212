## =====================================================
# pages/1_🏠_Property_Search.py
# =====================================================

import streamlit as st
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from utils.auth import initialize_auth_state
from utils.rentcast_api import fetch_property_details
from utils.database import get_user_usage
from streamlit.components.v1 import html
import os
from supabase import create_client, Client
import pandas as pd
from io import StringIO
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Property Search", page_icon="🏠", layout="wide")

# =====================================================
# 1. Supabase Connection & Setup
# =====================================================

@st.cache_resource
def get_supabase_client() -> Client:
    """Initialize and return Supabase client using auth state"""
    try:
        # Get Supabase credentials from auth state
        if not hasattr(st.session_state, 'supabase_url') or not hasattr(st.session_state, 'supabase_key'):
            logger.error("Missing Supabase credentials in session state")
            st.error("❌ Database configuration error. Please ensure Supabase credentials are set.")
            st.stop()
        
        supabase_url = st.session_state.supabase_url
        supabase_key = st.session_state.supabase_key
        
        if not supabase_url or not supabase_key:
            logger.error("Empty Supabase credentials")
            st.error("❌ Database configuration error. Please check your Supabase credentials.")
            st.stop()
        
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
        return supabase
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        st.error(f"❌ Database connection failed: {str(e)}")
        st.stop()

# Initialize Supabase client after auth state is available
def init_supabase():
    """Initialize Supabase client after authentication"""
    if hasattr(st.session_state, 'supabase_url') and hasattr(st.session_state, 'supabase_key'):
        return get_supabase_client()
    return None

# =====================================================
# 2. Enhanced Database Functions
# =====================================================

def save_property_search(user_id: str, property_data: Dict[Any, Any], search_query: str = "") -> Tuple[bool, Optional[int]]:
    """Save comprehensive property search to database with enhanced metadata"""
    try:
        # Extract key property information for indexing
        address = property_data.get('formattedAddress') or property_data.get('address', 'Unknown')
        property_type = property_data.get('propertyType', 'Unknown')
        city = property_data.get('city', '')
        state = property_data.get('state', '')
        zip_code = property_data.get('zipCode', '')
        
        # Extract numeric values safely
        bedrooms = safe_numeric_get(property_data, 'bedrooms')
        bathrooms = safe_numeric_get(property_data, 'bathrooms')
        square_footage = safe_numeric_get(property_data, 'squareFootage')
        estimated_value = safe_numeric_get(property_data, 'estimatedValue')
        year_built = safe_numeric_get(property_data, 'yearBuilt')
        
        # Prepare comprehensive search record
        search_record = {
            'user_id': user_id,
            'property_data': property_data,  # Full property data JSON
            'search_query': search_query,
            'search_date': datetime.now().isoformat(),
            
            # Indexed fields for efficient querying
            'property_address': address,
            'property_type': property_type,
            'city': city,
            'state': state,
            'zip_code': zip_code,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'square_footage': square_footage,
            'estimated_value': estimated_value,
            'year_built': year_built,
            
            # Additional metadata
            'data_completeness_score': calculate_data_completeness(property_data),
            'search_metadata': {
                'api_response_size': len(json.dumps(property_data)),
                'property_features_count': count_property_features(property_data),
                'has_history': bool(property_data.get('history')),
                'has_tax_data': bool(property_data.get('propertyTaxes')),
                'has_owner_info': bool(property_data.get('owner')),
                'has_market_data': bool(property_data.get('marketValue') or property_data.get('estimatedValue'))
            }
        }
        
        result = supabase.table('property_searches').insert(search_record).execute()
        
        if result.data:
            search_id = result.data[0]['id']
            logger.info(f"Property search saved successfully with ID: {search_id}")
            return True, search_id
        else:
            logger.error("Failed to save property search - no data returned")
            return False, None
            
    except Exception as e:
        logger.error(f"Error saving property search: {e}")
        return False, None

def get_user_property_searches(user_id: str, limit: int = 100, filters: Dict = None) -> List[Dict]:
    """Get user's property search history with advanced filtering"""
    try:
        query = supabase.table('property_searches').select('*').eq('user_id', user_id)
        
        # Apply filters if provided
        if filters:
            if filters.get('property_type'):
                query = query.eq('property_type', filters['property_type'])
            
            if filters.get('city'):
                query = query.ilike('city', f"%{filters['city']}%")
            
            if filters.get('state'):
                query = query.eq('state', filters['state'])
            
            if filters.get('min_bedrooms'):
                query = query.gte('bedrooms', filters['min_bedrooms'])
            
            if filters.get('max_bedrooms'):
                query = query.lte('bedrooms', filters['max_bedrooms'])
            
            if filters.get('min_value'):
                query = query.gte('estimated_value', filters['min_value'])
            
            if filters.get('max_value'):
                query = query.lte('estimated_value', filters['max_value'])
            
            if filters.get('date_from'):
                query = query.gte('search_date', filters['date_from'].isoformat())
            
            if filters.get('date_to'):
                query = query.lte('search_date', filters['date_to'].isoformat())
        
        result = query.order('search_date', desc=True).limit(limit).execute()
        
        if result.data:
            logger.info(f"Retrieved {len(result.data)} property searches for user {user_id}")
            return result.data
        else:
            return []
            
    except Exception as e:
        logger.error(f"Error fetching property searches: {e}")
        return []

def delete_property_search(search_id: int, user_id: str) -> bool:
    """Delete a specific property search with user verification"""
    try:
        result = supabase.table('property_searches').delete().eq('id', search_id).eq('user_id', user_id).execute()
        
        if result.data:
            logger.info(f"Property search {search_id} deleted successfully")
            return True
        else:
            logger.warning(f"Property search {search_id} not found or not owned by user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting property search: {e}")
        return False

def bulk_delete_property_searches(user_id: str, search_ids: List[int] = None) -> Tuple[bool, int]:
    """Delete multiple property searches or all user searches"""
    try:
        query = supabase.table('property_searches').delete().eq('user_id', user_id)
        
        if search_ids:
            query = query.in_('id', search_ids)
        
        result = query.execute()
        
        deleted_count = len(result.data) if result.data else 0
        logger.info(f"Bulk deleted {deleted_count} property searches for user {user_id}")
        return True, deleted_count
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        return False, 0

def get_enhanced_search_statistics(user_id: str) -> Dict[str, Any]:
    """Get comprehensive user search statistics"""
    try:
        # Get all searches for analysis
        all_searches = supabase.table('property_searches').select('*').eq('user_id', user_id).execute()
        
        if not all_searches.data:
            return {}
        
        searches = all_searches.data
        now = datetime.now()
        
        # Basic statistics
        total_searches = len(searches)
        recent_searches = len([s for s in searches if 
                             datetime.fromisoformat(s['search_date'].replace('Z', '+00:00')) >= now - timedelta(days=30)])
        
        # Property type analysis
        property_types = {}
        for search in searches:
            prop_type = search.get('property_type', 'Unknown')
            property_types[prop_type] = property_types.get(prop_type, 0) + 1
        
        # City analysis
        cities = {}
        for search in searches:
            city = search.get('city', 'Unknown')
            if city and city != 'Unknown':
                cities[city] = cities.get(city, 0) + 1
        
        # Value range analysis
        values = [s.get('estimated_value') for s in searches if s.get('estimated_value')]
        value_stats = {}
        if values:
            value_stats = {
                'min_value': min(values),
                'max_value': max(values),
                'avg_value': sum(values) / len(values),
                'median_value': sorted(values)[len(values) // 2]
            }
        
        # Bedroom analysis
        bedrooms = [s.get('bedrooms') for s in searches if s.get('bedrooms')]
        bedroom_stats = {}
        if bedrooms:
            bedroom_counts = {}
            for br in bedrooms:
                bedroom_counts[str(br)] = bedroom_counts.get(str(br), 0) + 1
            bedroom_stats = bedroom_counts
        
        # Data completeness analysis
        completeness_scores = [s.get('data_completeness_score', 0) for s in searches]
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        return {
            'total_searches': total_searches,
            'recent_searches': recent_searches,
            'top_property_types': sorted(property_types.items(), key=lambda x: x[1], reverse=True)[:5],
            'top_cities': sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10],
            'value_statistics': value_stats,
            'bedroom_distribution': bedroom_stats,
            'average_data_completeness': round(avg_completeness * 100, 1),
            'search_trends': calculate_search_trends(searches),
            'data_quality_metrics': calculate_data_quality_metrics(searches)
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced search statistics: {e}")
        return {}

def export_search_history(user_id: str, format_type: str = 'csv') -> Optional[str]:
    """Export user's complete search history in various formats"""
    try:
        searches = get_user_property_searches(user_id, limit=1000)
        
        if not searches:
            return None
        
        if format_type.lower() == 'csv':
            # Flatten data for CSV export
            flattened_data = []
            for search in searches:
                flat_record = {
                    'search_id': search['id'],
                    'search_date': search['search_date'],
                    'search_query': search.get('search_query', ''),
                    'property_address': search.get('property_address', ''),
                    'property_type': search.get('property_type', ''),
                    'city': search.get('city', ''),
                    'state': search.get('state', ''),
                    'zip_code': search.get('zip_code', ''),
                    'bedrooms': search.get('bedrooms', ''),
                    'bathrooms': search.get('bathrooms', ''),
                    'square_footage': search.get('square_footage', ''),
                    'estimated_value': search.get('estimated_value', ''),
                    'year_built': search.get('year_built', ''),
                    'data_completeness_score': search.get('data_completeness_score', '')
                }
                flattened_data.append(flat_record)
            
            df = pd.DataFrame(flattened_data)
            return df.to_csv(index=False)
        
        elif format_type.lower() == 'json':
            return json.dumps(searches, indent=2, default=str)
        
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error exporting search history: {e}")
        return None

# =====================================================
# 3. Enhanced Helper Functions
# =====================================================

def safe_get(data: Any, key: str, default: Any = "N/A") -> Any:
    """Safely get a value from dict with default fallback and type checking"""
    try:
        if isinstance(data, dict):
            value = data.get(key, default)
            if value is None or value == "" or value == []:
                return default
            return value
        return default
    except (AttributeError, TypeError, KeyError):
        return default

def safe_numeric_get(data: Dict, key: str, default: Optional[float] = None) -> Optional[float]:
    """Safely extract numeric values from property data"""
    try:
        value = safe_get(data, key)
        if value == "N/A" or value is None:
            return default
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove common formatting characters
            cleaned = value.replace(',', '').replace('$', '').replace(' sq ft', '').strip()
            if cleaned.replace('.', '').isdigit():
                return float(cleaned)
        
        return default
    except (ValueError, TypeError):
        return default

def format_currency(value: Any) -> str:
    """Enhanced currency formatting with better handling of various input types"""
    try:
        if value is None or value == "N/A":
            return "N/A"
        
        if isinstance(value, (int, float)) and value > 0:
            return f"${value:,.0f}"
        
        if isinstance(value, str):
            # Try to extract number from string
            import re
            numbers = re.findall(r'[\d,]+\.?\d*', value.replace('$', ''))
            if numbers:
                cleaned = numbers[0].replace(',', '')
                try:
                    num_value = float(cleaned)
                    return f"${num_value:,.0f}"
                except ValueError:
                    pass
        
        return "N/A"
    except (ValueError, TypeError):
        return "N/A"

def format_area(value: Any) -> str:
    """Format area/square footage values"""
    try:
        if value is None or value == "N/A":
            return "N/A"
        
        if isinstance(value, (int, float)) and value > 0:
            return f"{value:,.0f} sq ft"
        
        if isinstance(value, str) and value.replace(',', '').replace(' sq ft', '').isdigit():
            num_val = int(value.replace(',', '').replace(' sq ft', ''))
            return f"{num_val:,} sq ft"
        
        return str(value) if str(value) != "N/A" else "N/A"
    except (ValueError, TypeError):
        return "N/A"

def calculate_data_completeness(property_data: Dict) -> float:
    """Calculate data completeness score for a property"""
    try:
        key_fields = [
            'formattedAddress', 'address', 'propertyType', 'bedrooms', 'bathrooms',
            'squareFootage', 'yearBuilt', 'estimatedValue', 'marketValue', 'city',
            'state', 'zipCode', 'owner', 'history', 'propertyTaxes', 'features'
        ]
        
        filled_fields = 0
        for field in key_fields:
            value = safe_get(property_data, field)
            if value != "N/A" and value is not None and value != "" and value != []:
                if isinstance(value, dict) and value:
                    filled_fields += 1
                elif isinstance(value, list) and value:
                    filled_fields += 1
                elif not isinstance(value, (dict, list)):
                    filled_fields += 1
        
        return filled_fields / len(key_fields)
    except Exception:
        return 0.0

def count_property_features(property_data: Dict) -> int:
    """Count the number of property features available"""
    try:
        features = safe_get(property_data, 'features', {})
        if isinstance(features, dict):
            return len([v for v in features.values() if v and v != "N/A"])
        return 0
    except Exception:
        return 0

def calculate_search_trends(searches: List[Dict]) -> Dict[str, Any]:
    """Calculate search trends over time"""
    try:
        if not searches:
            return {}
        
        # Group searches by month
        monthly_counts = {}
        for search in searches:
            try:
                search_date = datetime.fromisoformat(search['search_date'].replace('Z', '+00:00'))
                month_key = search_date.strftime('%Y-%m')
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
            except Exception:
                continue
        
        # Calculate trend
        sorted_months = sorted(monthly_counts.items())
        trend = "stable"
        if len(sorted_months) >= 2:
            recent_avg = sum([count for _, count in sorted_months[-2:]]) / 2
            earlier_avg = sum([count for _, count in sorted_months[:-2]]) / max(1, len(sorted_months) - 2)
            
            if recent_avg > earlier_avg * 1.2:
                trend = "increasing"
            elif recent_avg < earlier_avg * 0.8:
                trend = "decreasing"
        
        return {
            'monthly_distribution': dict(sorted_months),
            'trend': trend,
            'most_active_month': max(monthly_counts.items(), key=lambda x: x[1]) if monthly_counts else None
        }
    except Exception:
        return {}

def calculate_data_quality_metrics(searches: List[Dict]) -> Dict[str, Any]:
    """Calculate data quality metrics across all searches"""
    try:
        if not searches:
            return {}
        
        total_searches = len(searches)
        
        # Count searches with various data types
        has_owner_info = len([s for s in searches if s.get('search_metadata', {}).get('has_owner_info', False)])
        has_history = len([s for s in searches if s.get('search_metadata', {}).get('has_history', False)])
        has_tax_data = len([s for s in searches if s.get('search_metadata', {}).get('has_tax_data', False)])
        has_market_data = len([s for s in searches if s.get('search_metadata', {}).get('has_market_data', False)])
        
        return {
            'owner_info_coverage': round((has_owner_info / total_searches) * 100, 1),
            'history_coverage': round((has_history / total_searches) * 100, 1),
            'tax_data_coverage': round((has_tax_data / total_searches) * 100, 1),
            'market_data_coverage': round((has_market_data / total_searches) * 100, 1)
        }
    except Exception:
        return {}

def build_card(title: str, content: str, card_type: str = "default") -> str:
    """Build enhanced HTML card component with different types"""
    type_classes = {
        "default": "card",
        "highlight": "card highlight",
        "warning": "card warning",
        "success": "card success",
        "info": "card info"
    }
    
    card_class = type_classes.get(card_type, "card")
    
    return f"""
    <div class="{card_class}">
        <h3>{title}</h3>
        <div class="content">{content}</div>
    </div>
    """

def build_compact_card(title: str, content: str, card_id: str = "") -> str:
    """Build compact HTML card for history view with enhanced styling"""
    return f"""
    <div class="compact-card" id="{card_id}">
        <h4>{title}</h4>
        <div class="compact-content">{content}</div>
    </div>
    """

def process_property_data(raw_data: Any) -> Optional[Dict]:
    """Enhanced property data processing with comprehensive data extraction"""
    try:
        logger.info(f"Processing raw API response (type: {type(raw_data)})")
        
        # Handle different response formats
        if isinstance(raw_data, str):
            try:
                property_data = json.loads(raw_data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return None
        elif isinstance(raw_data, (dict, list)):
            property_data = raw_data
        else:
            logger.error(f"Unexpected data type: {type(raw_data)}")
            return None
        
        if not property_data:
            logger.error("Empty property data received")
            return None
        
        # Extract property from various response structures
        properties = None
        
        if isinstance(property_data, list) and len(property_data) > 0:
            properties = property_data
        elif isinstance(property_data, dict):
            # Try different possible keys for property data
            for key in ["properties", "data", "results", "property"]:
                if key in property_data:
                    if isinstance(property_data[key], list) and property_data[key]:
                        properties = property_data[key]
                        break
                    elif isinstance(property_data[key], dict):
                        properties = [property_data[key]]
                        break
            
            # If no nested structure found, check if this is already a property object
            if not properties:
                required_fields = ["formattedAddress", "address", "propertyType", "bedrooms"]
                if any(field in property_data for field in required_fields):
                    properties = [property_data]
        
        if not properties or len(properties) == 0:
            logger.error("No properties found in response")
            return None
        
        first_property = properties[0]
        
        # Enhance property data with additional processing
        enhanced_property = enhance_property_data(first_property)
        
        logger.info(f"Successfully processed property: {enhanced_property.get('formattedAddress', 'Unknown Address')}")
        return enhanced_property
        
    except Exception as e:
        logger.error(f"Error processing property data: {e}")
        return None

def enhance_property_data(property_data: Dict) -> Dict:
    """Enhance property data with computed fields and standardization"""
    try:
        enhanced = property_data.copy()
        
        # Standardize address formatting
        if not enhanced.get('formattedAddress') and enhanced.get('address'):
            enhanced['formattedAddress'] = enhanced['address']
        
        # Ensure numeric fields are properly typed
        numeric_fields = ['bedrooms', 'bathrooms', 'squareFootage', 'yearBuilt', 'estimatedValue', 'marketValue']
        for field in numeric_fields:
            if field in enhanced:
                enhanced[field] = safe_numeric_get(enhanced, field)
        
        # Add computed fields
        enhanced['_computed_fields'] = {
            'price_per_sqft': calculate_price_per_sqft(enhanced),
            'property_age': calculate_property_age(enhanced),
            'size_category': categorize_property_size(enhanced),
            'value_category': categorize_property_value(enhanced)
        }
        
        # Standardize boolean fields
        boolean_fields = ['hasPool', 'hasGarage', 'hasFireplace', 'hasDeck', 'hasBasement']
        for field in boolean_fields:
            if field in enhanced:
                enhanced[field] = bool(enhanced[field])
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing property data: {e}")
        return property_data

def calculate_price_per_sqft(property_data: Dict) -> Optional[float]:
    """Calculate price per square foot"""
    try:
        value = safe_numeric_get(property_data, 'estimatedValue')
        sqft = safe_numeric_get(property_data, 'squareFootage')
        
        if value and sqft and sqft > 0:
            return round(value / sqft, 2)
        return None
    except Exception:
        return None

def calculate_property_age(property_data: Dict) -> Optional[int]:
    """Calculate property age in years"""
    try:
        year_built = safe_numeric_get(property_data, 'yearBuilt')
        if year_built:
            current_year = datetime.now().year
            return current_year - int(year_built)
        return None
    except Exception:
        return None

def categorize_property_size(property_data: Dict) -> str:
    """Categorize property by size"""
    try:
        sqft = safe_numeric_get(property_data, 'squareFootage')
        if not sqft:
            return "Unknown"
        
        if sqft < 1000:
            return "Small"
        elif sqft < 2000:
            return "Medium"
        elif sqft < 3500:
            return "Large"
        else:
            return "Very Large"
    except Exception:
        return "Unknown"

def categorize_property_value(property_data: Dict) -> str:
    """Categorize property by estimated value"""
    try:
        value = safe_numeric_get(property_data, 'estimatedValue')
        if not value:
            return "Unknown"
        
        if value < 200000:
            return "Budget"
        elif value < 500000:
            return "Mid-Range"
        elif value < 1000000:
            return "High-End"
        else:
            return "Luxury"
    except Exception:
        return "Unknown"

def render_comprehensive_property_cards(prop: Dict[Any, Any], compact: bool = False) -> str:
    """Render comprehensive property information as HTML cards"""
    cards_html = ""
    card_function = build_compact_card if compact else build_card
    
    # Basic Property Information (Enhanced)
    basic_info = f"""
    <b>Property Type:</b> {safe_get(prop, 'propertyType')}<br>
    <b>Bedrooms:</b> {safe_get(prop, 'bedrooms')}<br>
    <b>Bathrooms:</b> {safe_get(prop, 'bathrooms')}<br>
    <b>Square Footage:</b> {format_area(safe_get(prop, 'squareFootage'))}<br>
    <b>Year Built:</b> {safe_get(prop, 'yearBuilt')}<br>
    """
    
    # Add computed fields if available
    computed = safe_get(prop, '_computed_fields', {})
    if computed.get('property_age'):
        basic_info += f"<b>Property Age:</b> {computed['property_age']} years<br>"
    if computed.get('size_category'):
        basic_info += f"<b>Size Category:</b> {computed['size_category']}<br>"
    
    cards_html += card_function("🏠 Property Details", basic_info)

    # Address Information (Enhanced)
    address_info = f"""
    <b>Full Address:</b> {safe_get(prop, 'formattedAddress', safe_get(prop, 'address'))}<br>
    <b>City:</b> {safe_get(prop, 'city')}<br>
    <b>State:</b> {safe_get(prop, 'state')}<br>
    <b>ZIP Code:</b> {safe_get(prop, 'zipCode')}<br>
    <b>County:</b> {safe_get(prop, 'county')}<br>
    """
    
    # Add coordinates if available
    if safe_get(prop, 'latitude') != "N/A" and safe_get(prop, 'longitude') != "N/A":
        lat, lng = safe_get(prop, 'latitude'), safe_get(prop, 'longitude')
        address_info += f"<b>Coordinates:</b> {lat}, {lng}<br>"
    
    cards_html += card_function("📍 Location Information", address_info)

    # Comprehensive Valuation Information
    valuation_info = ""
    estimated_value = safe_get(prop, 'estimatedValue')
    market_value = safe_get(prop, 'marketValue')
    
    if estimated_value != "N/A":
        valuation_info += f"<b>Estimated Value:</b> {format_currency(estimated_value)}<br>"
    
    if market_value != "N/A":
        valuation_info += f"<b>Market Value:</b> {format_currency(market_value)}<br>"
    
    # Add price per square foot if available
    if computed.get('price_per_sqft'):
        valuation_info += f"<b>Price per Sq Ft:</b> ${computed['price_per_sqft']}<br>"
    
    if computed.get('value_category'):
        valuation_info += f"<b>Value Category:</b> {computed['value_category']}<br>"
    
    # Add rental estimates if available
    rental_estimate = safe_get(prop, 'rentalEstimate')
    if rental_estimate != "N/A":
        if isinstance(rental_estimate, dict):
            rent_amount = rental_estimate.get('amount') or rental_estimate.get('estimate')
            if rent_amount:
                valuation_info += f"<b>Rental Estimate:</b> {format_currency(rent_amount)}/month<br>"
        else:
            valuation_info += f"<b>Rental Estimate:</b> {format_currency(rental_estimate)}/month<br>"
    
    if valuation_info:
        cards_html += card_function("💰 Valuation & Financial", valuation_info)

    if not compact:
        # Detailed Property Features & Amenities
        features = safe_get(prop, 'features')
        if features != "N/A" and isinstance(features, dict):
            features_html = ""
            feature_categories = {
                'Interior': ['fireplace', 'hardwoodFloors', 'updatedKitchen', 'centralAir', 'basement', 'attic'],
                'Exterior': ['pool', 'garage', 'deck', 'patio', 'fencing', 'landscaping'],
                'Utilities': ['heating', 'cooling', 'water', 'sewer', 'electrical', 'internet'],
                'Security': ['alarmSystem', 'gatedCommunity', 'securityLighting'],
                'Other': ['newConstruction', 'recentRenovation', 'energyEfficient']
            }
            
            for category, feature_list in feature_categories.items():
                category_features = []
                for feature in feature_list:
                    if feature in features and features[feature]:
                        category_features.append(f"{feature.replace('_', ' ').title()}: {features[feature]}")
                
                if category_features:
                    features_html += f"<b>{category}:</b><br>"
                    features_html += "<br>".join([f"&nbsp;&nbsp;• {f}" for f in category_features])
                    features_html += "<br><br>"
            
            # Add any remaining features not categorized
            remaining_features = {k: v for k, v in features.items() 
                               if k not in [item for sublist in feature_categories.values() for item in sublist] 
                               and v and v != "N/A"}
            
            if remaining_features:
                features_html += "<b>Additional Features:</b><br>"
                features_html += "<br>".join([
                    f"&nbsp;&nbsp;• <b>{k.replace('_', ' ').title()}:</b> {v}" 
                    for k, v in remaining_features.items()
                ])
            
            if features_html:
                cards_html += card_function("🔧 Features & Amenities", features_html)

        # Comprehensive Property Taxes
        property_taxes = safe_get(prop, 'propertyTaxes')
        if property_taxes != "N/A" and isinstance(property_taxes, dict):
            tax_html = ""
            total_taxes = 0
            tax_count = 0
            
            for year, tax_data in sorted(property_taxes.items(), reverse=True):
                if isinstance(tax_data, dict):
                    total = safe_numeric_get(tax_data, 'total', 0)
                    assessed = safe_numeric_get(tax_data, 'assessedValue', 0)
                    
                    if total:
                        tax_html += f"<b>{year}:</b><br>"
                        tax_html += f"&nbsp;&nbsp;• Total Tax: {format_currency(total)}<br>"
                        if assessed:
                            tax_html += f"&nbsp;&nbsp;• Assessed Value: {format_currency(assessed)}<br>"
                            if assessed > 0:
                                tax_rate = (total / assessed) * 100
                                tax_html += f"&nbsp;&nbsp;• Effective Tax Rate: {tax_rate:.2f}%<br>"
                        tax_html += "<br>"
                        
                        total_taxes += total
                        tax_count += 1
                        
                elif isinstance(tax_data, (int, float)) and tax_data > 0:
                    tax_html += f"<b>{year}:</b> {format_currency(tax_data)}<br>"
                    total_taxes += tax_data
                    tax_count += 1
            
            # Add average if we have multiple years
            if tax_count > 1:
                avg_tax = total_taxes / tax_count
                tax_html += f"<b>Average Annual Tax ({tax_count} years):</b> {format_currency(avg_tax)}<br>"
            
            if tax_html:
                cards_html += card_function("🏛️ Property Tax History", tax_html)

        # Comprehensive Sale History
        history = safe_get(prop, 'history')
        if history != "N/A" and isinstance(history, (dict, list)):
            hist_html = ""
            
            if isinstance(history, dict):
                # Handle dict format
                for event_key, event_data in sorted(history.items(), key=lambda x: x[1].get('date', ''), reverse=True):
                    if isinstance(event_data, dict):
                        event_type = event_data.get('event', event_data.get('type', 'Sale'))
                        date = event_data.get('date', 'Unknown Date')
                        price = safe_numeric_get(event_data, 'price', 0)
                        source = event_data.get('source', '')
                        
                        hist_html += f"<b>{event_type}:</b><br>"
                        hist_html += f"&nbsp;&nbsp;• Date: {date}<br>"
                        if price:
                            hist_html += f"&nbsp;&nbsp;• Price: {format_currency(price)}<br>"
                        if source:
                            hist_html += f"&nbsp;&nbsp;• Source: {source}<br>"
                        hist_html += "<br>"
                        
            elif isinstance(history, list):
                # Handle list format
                sorted_history = sorted(history, key=lambda x: x.get('date', ''), reverse=True)
                for event in sorted_history:
                    if isinstance(event, dict):
                        event_type = event.get('event', event.get('type', 'Sale'))
                        date = event.get('date', 'Unknown Date')
                        price = safe_numeric_get(event, 'price', 0)
                        source = event.get('source', '')
                        description = event.get('description', '')
                        
                        hist_html += f"<b>{event_type}:</b><br>"
                        hist_html += f"&nbsp;&nbsp;• Date: {date}<br>"
                        if price:
                            hist_html += f"&nbsp;&nbsp;• Price: {format_currency(price)}<br>"
                        if source:
                            hist_html += f"&nbsp;&nbsp;• Source: {source}<br>"
                        if description:
                            hist_html += f"&nbsp;&nbsp;• Details: {description}<br>"
                        hist_html += "<br>"
            
            if hist_html:
                cards_html += card_function("📜 Transaction History", hist_html)

        # Comprehensive Owner Information
        owner = safe_get(prop, 'owner')
        if owner != "N/A" and isinstance(owner, dict):
            owner_html = ""
            
            names = owner.get('names', owner.get('name', []))
            if isinstance(names, str):
                names = [names]
            if names:
                owner_html += f"<b>Owner(s):</b> {', '.join(names)}<br>"
            
            # Add additional owner details if available
            owner_type = owner.get('type', owner.get('ownerType'))
            if owner_type:
                owner_html += f"<b>Owner Type:</b> {owner_type}<br>"
            
            mailing_address = owner.get('mailingAddress')
            if mailing_address and mailing_address != safe_get(prop, 'formattedAddress'):
                owner_html += f"<b>Mailing Address:</b> {mailing_address}<br>"
            
            ownership_date = owner.get('ownershipDate')
            if ownership_date:
                owner_html += f"<b>Ownership Since:</b> {ownership_date}<br>"
            
            if owner_html:
                cards_html += card_function("👤 Owner Information", owner_html)

        # Market Analysis & Comparables
        market_data = safe_get(prop, 'marketAnalysis')
        if market_data != "N/A" and isinstance(market_data, dict):
            market_html = ""
            
            comparable_sales = market_data.get('comparableSales', [])
            if comparable_sales:
                market_html += f"<b>Comparable Sales:</b><br>"
                for comp in comparable_sales[:3]:  # Show top 3 comparables
                    if isinstance(comp, dict):
                        comp_address = comp.get('address', 'Unknown Address')
                        comp_price = format_currency(comp.get('price', 0))
                        comp_date = comp.get('saleDate', 'Unknown Date')
                        market_html += f"&nbsp;&nbsp;• {comp_address}: {comp_price} ({comp_date})<br>"
            
            market_trends = market_data.get('trends')
            if market_trends and isinstance(market_trends, dict):
                market_html += "<br><b>Market Trends:</b><br>"
                for key, value in market_trends.items():
                    if value:
                        market_html += f"&nbsp;&nbsp;• {key.replace('_', ' ').title()}: {value}<br>"
            
            if market_html:
                cards_html += card_function("📈 Market Analysis", market_html)

        # Neighborhood Information
        neighborhood = safe_get(prop, 'neighborhood')
        if neighborhood != "N/A" and isinstance(neighborhood, dict):
            neighborhood_html = ""
            
            # School information
            schools = neighborhood.get('schools', [])
            if schools:
                neighborhood_html += "<b>Schools:</b><br>"
                for school in schools:
                    if isinstance(school, dict):
                        school_name = school.get('name', 'Unknown School')
                        school_type = school.get('type', '')
                        school_rating = school.get('rating', '')
                        school_distance = school.get('distance', '')
                        
                        school_info = f"&nbsp;&nbsp;• {school_name}"
                        if school_type:
                            school_info += f" ({school_type})"
                        if school_rating:
                            school_info += f" - Rating: {school_rating}"
                        if school_distance:
                            school_info += f" - {school_distance}"
                        neighborhood_html += school_info + "<br>"
                neighborhood_html += "<br>"
            
            # Demographics
            demographics = neighborhood.get('demographics')
            if demographics and isinstance(demographics, dict):
                neighborhood_html += "<b>Demographics:</b><br>"
                for key, value in demographics.items():
                    if value:
                        neighborhood_html += f"&nbsp;&nbsp;• {key.replace('_', ' ').title()}: {value}<br>"
                neighborhood_html += "<br>"
            
            # Local amenities
            amenities = neighborhood.get('amenities', [])
            if amenities:
                neighborhood_html += f"<b>Nearby Amenities:</b> {', '.join(amenities)}<br>"
            
            if neighborhood_html:
                cards_html += card_function("🏘️ Neighborhood Info", neighborhood_html)

        # Environmental & Risk Information
        environmental = safe_get(prop, 'environmental')
        if environmental != "N/A" and isinstance(environmental, dict):
            env_html = ""
            
            flood_risk = environmental.get('floodRisk')
            if flood_risk:
                env_html += f"<b>Flood Risk:</b> {flood_risk}<br>"
            
            earthquake_risk = environmental.get('earthquakeRisk')
            if earthquake_risk:
                env_html += f"<b>Earthquake Risk:</b> {earthquake_risk}<br>"
            
            fire_risk = environmental.get('fireRisk')
            if fire_risk:
                env_html += f"<b>Fire Risk:</b> {fire_risk}<br>"
            
            climate_data = environmental.get('climate')
            if climate_data and isinstance(climate_data, dict):
                env_html += "<b>Climate Information:</b><br>"
                for key, value in climate_data.items():
                    if value:
                        env_html += f"&nbsp;&nbsp;• {key.replace('_', ' ').title()}: {value}<br>"
            
            if env_html:
                cards_html += card_function("🌍 Environmental & Risk Factors", env_html)

        # Utilities & Services
        utilities = safe_get(prop, 'utilities')
        if utilities != "N/A" and isinstance(utilities, dict):
            utilities_html = ""
            
            for utility_type, utility_info in utilities.items():
                if utility_info and utility_info != "N/A":
                    utilities_html += f"<b>{utility_type.replace('_', ' ').title()}:</b> {utility_info}<br>"
            
            if utilities_html:
                cards_html += card_function("⚡ Utilities & Services", utilities_html)

        # Additional Property Details
        additional_details = {}
        detail_fields = [
            'lotSize', 'parking', 'construction', 'roofType', 'foundationType',
            'heatingType', 'coolingType', 'plumbingType', 'electricalType'
        ]
        
        for field in detail_fields:
            value = safe_get(prop, field)
            if value != "N/A":
                additional_details[field] = value
        
        if additional_details:
            details_html = ""
            for key, value in additional_details.items():
                details_html += f"<b>{key.replace('_', ' ').title()}:</b> {value}<br>"
            
            cards_html += card_function("🔍 Additional Details", details_html)

    # Always include raw JSON data for transparency and debugging
    try:
        # Create a clean version of the property data for display
        display_data = prop.copy()
        
        # Remove or truncate very large nested objects for better readability
        for key in display_data:
            if isinstance(display_data[key], dict) and len(str(display_data[key])) > 1000:
                display_data[key] = f"[Large object with {len(display_data[key])} keys - view in full export]"
            elif isinstance(display_data[key], list) and len(str(display_data[key])) > 1000:
                display_data[key] = f"[Large array with {len(display_data[key])} items - view in full export]"
        
        pretty_json = json.dumps(display_data, indent=2, default=str)
        if len(pretty_json) > 8000:
            pretty_json = pretty_json[:8000] + "\n\n... (truncated - use export feature for complete data)"
        
        cards_html += card_function("📋 Raw Property Data", f"<pre>{pretty_json}</pre>", "info")
        
    except Exception as e:
        cards_html += card_function("📋 Raw Property Data", f"<pre>Error displaying JSON: {str(e)}</pre>", "warning")

    return cards_html

# =====================================================
# 4. Initialize Auth & Supabase Connection
# =====================================================
initialize_auth_state()

if st.session_state.user is None:
    st.warning("⚠️ Please log in from the main page to access this feature.")
    st.stop()

# Initialize Supabase client after authentication
supabase = init_supabase()
if not supabase:
    st.error("❌ Failed to initialize database connection. Please try logging in again.")
    st.stop()

user_email = st.session_state.user.email
user_id = st.session_state.user.id

# =====================================================
# 5. Enhanced Sidebar with Comprehensive Analytics
# =====================================================
with st.sidebar:
    st.subheader("👤 Account Dashboard")
    
    # Verify Supabase connection before proceeding
    if not supabase:
        st.error("❌ Database connection required")
        st.stop()
    
    queries_used = get_user_usage(user_id, user_email)
    
    st.metric("Email", user_email)
    st.metric("API Queries Used", f"{queries_used}/30")
    
    # Usage warnings with progress bar
    usage_percentage = (queries_used / 30) * 100
    st.progress(usage_percentage / 100)
    
    if queries_used >= 30:
        st.error("🚫 Monthly limit reached!")
    elif queries_used >= 25:
        st.warning("⚠️ Approaching monthly limit!")
    elif queries_used >= 20:
        st.info("ℹ️ 67% of monthly queries used")
    
    # Enhanced Search Statistics
    st.subheader("📊 Search Analytics")
    stats = get_enhanced_search_statistics(user_id)
    
    if stats:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Searches", stats.get('total_searches', 0))
            st.metric("Last 30 Days", stats.get('recent_searches', 0))
        
        with col2:
            st.metric("Avg Data Quality", f"{stats.get('average_data_completeness', 0)}%")
            trend = stats.get('search_trends', {}).get('trend', 'stable')
            st.metric("Search Trend", trend.title())
        
        # Top property types
        if stats.get('top_property_types'):
            st.subheader("🏠 Property Types")
            for prop_type, count in stats['top_property_types']:
                st.text(f"{prop_type}: {count}")
        
        # Top cities
        if stats.get('top_cities'):
            st.subheader("🌆 Top Cities")
            for city, count in stats['top_cities'][:5]:
                st.text(f"{city}: {count}")
        
        # Value statistics
        if stats.get('value_statistics'):
            st.subheader("💰 Value Range")
            value_stats = stats['value_statistics']
            st.text(f"Min: {format_currency(value_stats.get('min_value', 0))}")
            st.text(f"Max: {format_currency(value_stats.get('max_value', 0))}")
            st.text(f"Avg: {format_currency(value_stats.get('avg_value', 0))}")
        
        # Data quality metrics
        if stats.get('data_quality_metrics'):
            st.subheader("📈 Data Coverage")
            quality_metrics = stats['data_quality_metrics']
            st.text(f"Owner Info: {quality_metrics.get('owner_info_coverage', 0)}%")
            st.text(f"History: {quality_metrics.get('history_coverage', 0)}%")
            st.text(f"Tax Data: {quality_metrics.get('tax_data_coverage', 0)}%")
            st.text(f"Market Data: {quality_metrics.get('market_data_coverage', 0)}%")

    # Quick actions
    st.subheader("⚡ Quick Actions")
    if st.button("📤 Export All Data", help="Export complete search history"):
        st.session_state.show_export_options = True
    
    if st.button("🔄 Refresh Stats", help="Update search statistics"):
        st.cache_resource.clear()
        st.rerun()

# =====================================================
# 6. Export Modal (if triggered)
# =====================================================
if st.session_state.get('show_export_options', False):
    with st.sidebar:
        st.subheader("📤 Export Options")
        
        export_format = st.selectbox("Format", ["CSV", "JSON"])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬇️ Download"):
                export_data = export_search_history(user_id, export_format.lower())
                if export_data:
                    filename = f"property_searches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format.lower()}"
                    st.download_button(
                        label=f"📄 Download {export_format}",
                        data=export_data,
                        file_name=filename,
                        mime="text/csv" if export_format == "CSV" else "application/json"
                    )
                else:
                    st.error("No data to export")
        
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.show_export_options = False
                st.rerun()

# =====================================================
# 7. Enhanced Tab Layout
# =====================================================
tab1, tab2, tab3 = st.tabs(["🔍 Property Search", "📚 Search History", "📊 Analytics Dashboard"])

# =====================================================
# 8. NEW SEARCH TAB (Enhanced)
# =====================================================
with tab1:
    st.title("🏠 Advanced Property Search")
    st.markdown("Comprehensive property analysis with detailed market insights, ownership history, and neighborhood data.")

    # Enhanced search input with suggestions
    col1, col2 = st.columns([3, 1])
    
    with col1:
        address = st.text_input(
            "Enter Property Address",
            placeholder="e.g., 123 Main St, New York, NY 10001 or 1234 Oak Avenue, Los Angeles, CA 90210",
            help="Enter a complete address for best results. Include street number, street name, city, state, and ZIP code."
        )
    
    with col2:
        search_options = st.expander("🔧 Search Options")
        with search_options:
            save_search = st.checkbox("Save to history", value=True, help="Automatically save successful searches")
            detailed_analysis = st.checkbox("Detailed analysis", value=True, help="Include comprehensive property analysis")

    # Search button with enhanced feedback
    if st.button("🔍 Search Property", type="primary", use_container_width=True):
        if not address.strip():
            st.error("❌ Please enter a property address to search.")
        else:
            # Validate address format
            if len(address.strip()) < 10:
                st.warning("⚠️ Address seems too short. Please provide a complete address for better results.")
            
            search_start_time = datetime.now()
            
            with st.spinner("🔎 Fetching comprehensive property data..."):
                try:
                    # Show progress steps
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("📡 Connecting to property database...")
                    progress_bar.progress(25)
                    
                    # Fetch raw data from API
                    raw_response = fetch_property_details(address.strip(), user_id, user_email)
                    
                    status_text.text("📊 Processing property information...")
                    progress_bar.progress(50)
                    
                    if not raw_response:
                        st.error("⚠️ No response from property database. Please try again or check your address format.")
                        st.stop()
                    
                    status_text.text("🏠 Analyzing property details...")
                    progress_bar.progress(75)
                    
                    # Process the response with enhanced processing
                    prop = process_property_data(raw_response)
                    
                    if not prop:
                        st.error("⚠️ No property data found. Please verify the address and try again.")
                        with st.expander("🔍 Debug Information"):
                            st.subheader("Raw API Response")
                            response_str = str(raw_response)
                            st.code(response_str[:3000] + "..." if len(response_str) > 3000 else response_str)
                        st.stop()
                    
                    status_text.text("💾 Finalizing results...")
                    progress_bar.progress(100)
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Calculate search performance metrics
                    search_duration = (datetime.now() - search_start_time).total_seconds()
                    
                    # Display success message with metrics
                    property_address = safe_get(prop, 'formattedAddress', safe_get(prop, 'address', address))
                    data_completeness = calculate_data_completeness(prop)
                    
                    success_col1, success_col2, success_col3 = st.columns(3)
                    with success_col1:
                        st.success(f"✅ Property Found!")
                    with success_col2:
                        st.info(f"⏱️ Search time: {search_duration:.1f}s")
                    with success_col3:
                        st.info(f"📊 Data quality: {data_completeness*100:.1f}%")
                    
                    st.markdown(f"**📍 Address:** {property_address}")

                    # Save to database if enabled
                    if save_search:
                        save_success, search_id = save_property_search(user_id, prop, address.strip())
                        if save_success:
                            st.success(f"💾 Search saved to history! (ID: {search_id})")
                        else:
                            st.warning("⚠️ Could not save search to history (search completed successfully)")

                    # Build and render comprehensive property cards
                    cards_html = render_comprehensive_property_cards(prop, compact=False)
                    
                    if not cards_html:
                        st.warning("⚠️ No displayable property information found in the response.")
                    else:
                        # Enhanced CSS with better responsive design
                        full_html = f"""
                        <style>
                            body {{
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                color: #2c3e50;
                                background-color: #f8f9fa;
                                line-height: 1.6;
                            }}
                            .container {{
                                display: grid;
                                grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
                                gap: 24px;
                                padding: 16px;
                                max-width: 1400px;
                                margin: 0 auto;
                            }}
                            .card {{
                                background: linear-gradient(145deg, #ffffff, #f8f9fa);
                                padding: 28px;
                                border-radius: 16px;
                                box-shadow: 0 8px 32px rgba(0,0,0,0.08);
                                transition: all 0.4s ease;
                                border: 1px solid #e9ecef;
                                position: relative;
                                overflow: hidden;
                            }}
                            .card::before {{
                                content: '';
                                position: absolute;
                                top: 0;
                                left: 0;
                                right: 0;
                                height: 4px;
                                background: linear-gradient(90deg, #3498db, #2ecc71, #f39c12, #e74c3c);
                            }}
                            .card:hover {{
                                transform: translateY(-8px);
                                box-shadow: 0 16px 48px rgba(0,0,0,0.12);
                            }}
                            .card.highlight {{
                                background: linear-gradient(145deg, #fff3cd, #ffeaa7);
                                border-color: #f39c12;
                            }}
                            .card.success {{
                                background: linear-gradient(145deg, #d4edda, #a8e6a3);
                                border-color: #2ecc71;
                            }}
                            .card.info {{
                                background: linear-gradient(145deg, #d1ecf1, #85c1e9);
                                border-color: #3498db;
                            }}
                            .card.warning {{
                                background: linear-gradient(145deg, #fff3cd, #ffeaa7);
                                border-color: #f39c12;
                            }}
                            .card h3 {{
                                margin-top: 0;
                                margin-bottom: 20px;
                                color: #2c3e50;
                                font-size: 22px;
                                font-weight: 700;
                                border-bottom: 3px solid #3498db;
                                padding-bottom: 12px;
                                display: flex;
                                align-items: center;
                                gap: 8px;
                            }}
                            .content {{
                                font-size: 15px;
                                line-height: 1.8;
                                color: #495057;
                            }}
                            .content b {{
                                color: #2c3e50;
                                font-weight: 600;
                            }}
                            .content br {{
                                line-height: 2;
                            }}
                            pre {{
                                white-space: pre-wrap;
                                word-wrap: break-word;
                                background: #f8f9fa;
                                padding: 20px;
                                border-radius: 12px;
                                font-size: 12px;
                                border: 1px solid #dee2e6;
                                max-height: 500px;
                                overflow-y: auto;
                                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                            }}
                            @media (max-width: 768px) {{
                                .container {{
                                    grid-template-columns: 1fr;
                                    padding: 12px;
                                    gap: 20px;
                                }}
                                .card {{
                                    padding: 20px;
                                }}
                                .card h3 {{
                                    font-size: 20px;
                                }}
                            }}
                            @media (max-width: 480px) {{
                                .card {{
                                    padding: 16px;
                                }}
                                .content {{
                                    font-size: 14px;
                                }}
                            }}
                        </style>
                        <div class="container">
                            {cards_html}
                        </div>
                        """
                        
                        html(full_html, height=1400, scrolling=True)

                    # Additional action buttons
                    st.markdown("---")
                    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                    
                    with action_col1:
                        if st.button("📄 Export JSON", help="Export complete property data as JSON"):
                            json_data = json.dumps(prop, indent=2, default=str)
                            st.download_button(
                                label="⬇️ Download JSON",
                                data=json_data,
                                file_name=f"property_{property_address.replace(' ', '_').replace(',', '')}.json",
                                mime="application/json"
                            )
                    
                    with action_col2:
                        if st.button("📊 Generate Report", help="Create a formatted property report"):
                            st.info("📋 Report generation feature coming soon!")
                    
                    with action_col3:
                        if st.button("🔄 Refresh Data", help="Fetch updated property information"):
                            st.rerun()
                    
                    with action_col4:
                        if st.button("📌 Save Favorite", help="Add to favorite properties"):
                            st.info("⭐ Favorites feature coming soon!")

                except Exception as e:
                    logger.error(f"Error in property search: {e}")
                    st.error(f"❌ Error fetching property data: {str(e)}")
                    
                    with st.expander("🔍 Debug Information"):
                        st.subheader("Error Details")
                        st.text(f"Error Type: {type(e).__name__}")
                        st.text(f"Error Message: {str(e)}")
                        st.text(f"Search Query: {address}")
                        st.text(f"User ID: {user_id}")
                        
                        st.subheader("Stack Trace")
                        import traceback
                        st.code(traceback.format_exc())
                        
                        if 'raw_response' in locals():
                            st.subheader("Raw API Response")
                            response_str = str(raw_response)
                            st.code(response_str[:3000] + "..." if len(response_str) > 3000 else response_str)

    # Enhanced tips section
    st.markdown("---")
    
    tips_col1, tips_col2 = st.columns(2)
    
    with tips_col1:
        st.subheader("💡 Search Tips")
        st.markdown("""
        **For Best Results:**
        - Include **complete address** with city, state, ZIP
        - Use standard formatting: `123 Main St, City, ST 12345`
        - Double-check **spelling** of street/city names
        - For condos/apartments, include **unit numbers**
        - Try variations if no results found
        """)
    
    with tips_col2:
        st.subheader("📊 Data Includes")
        st.markdown("""
        **Comprehensive Analysis:**
        - Property details & specifications
        - Market valuation & rental estimates
        - Sales history & tax records
        - Owner information & neighborhood data
        - Environmental factors & risk assessment
        - Features, amenities & utilities
        """)
    
    # Sample addresses for testing
    with st.expander("🧪 Try Sample Addresses"):
        sample_addresses = [
            "123 Main Street, New York, NY 10001",
            "456 Oak Avenue, Los Angeles, CA 90210",
            "789 Pine Street, Chicago, IL 60601",
            "321 Elm Street, Miami, FL 33101",
            "654 Maple Drive, Houston, TX 77001"
        ]
        
        st.markdown("**Click to use these sample addresses:**")
        for sample in sample_addresses:
            if st.button(f"📍 {sample}", key=f"sample_{sample}"):
                st.session_state.sample_address = sample
                st.rerun()
        
        if hasattr(st.session_state, 'sample_address'):
            st.info(f"Selected: {st.session_state.sample_address}")
            if st.button("🔄 Clear Selection"):
                delattr(st.session_state, 'sample_address')
                st.rerun()

# =====================================================
# 9. ENHANCED SEARCH HISTORY TAB
# =====================================================
with tab2:
    st.title("📚 Property Search History")
    st.markdown("Comprehensive view and management of all your property searches with advanced filtering and analysis.")

    # Fetch search history
    search_history = get_user_property_searches(user_id)
    
    if not search_history:
        st.info("📭 No search history found. Start searching for properties to build your comprehensive history!")
    else:
        # Advanced search filters
        st.subheader("🔍 Filter & Sort")
        
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            address_filter = st.text_input("🏠 Filter by address", placeholder="Type to filter addresses...")
            city_filter = st.selectbox("🌆 Filter by city", ["All Cities"] + 
                                     sorted(list(set([s.get('city', 'Unknown') for s in search_history 
                                                   if s.get('city') and s.get('city') != 'Unknown']))))
        
        with filter_col2:
            property_type_filter = st.selectbox("🏠 Filter by property type", ["All Types"] + 
                                              sorted(list(set([s.get('property_type', 'Unknown') for s in search_history 
                                                            if s.get('property_type') and s.get('property_type') != 'Unknown']))))
            
            date_filter = st.selectbox("📅 Filter by date", 
                                     ["All time", "Last 7 days", "Last 30 days", "Last 90 days", "Last year"])
        
        with filter_col3:
            min_value = st.number_input("💰 Min value", min_value=0, value=0, step=10000, format="%d")
            max_value = st.number_input("💰 Max value", min_value=0, value=0, step=10000, format="%d")
            
            sort_by = st.selectbox("📊 Sort by", 
                                 ["Search Date (Newest)", "Search Date (Oldest)", "Property Value (High to Low)", 
                                  "Property Value (Low to High)", "Address (A-Z)", "Property Type"])

        # Apply filters
        filtered_history = search_history.copy()
        
        # Apply all filters
        if city_filter != "All Cities":
            filtered_history = [s for s in filtered_history if s.get('city') == city_filter]
        
        if property_type_filter != "All Types":
            filtered_history = [s for s in filtered_history if s.get('property_type') == property_type_filter]
        
        if address_filter:
            filtered_history = [s for s in filtered_history 
                              if address_filter.lower() in (s.get('property_address', '') or '').lower()]
        
        # Date filter
        if date_filter != "All time":
            days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90, "Last year": 365}
            cutoff_date = datetime.now() - timedelta(days=days_map[date_filter])
            filtered_history = [s for s in filtered_history 
                              if datetime.fromisoformat(s['search_date'].replace('Z', '+00:00')) >= cutoff_date]
        
        # Value filters
        if min_value > 0:
            filtered_history = [s for s in filtered_history 
                              if s.get('estimated_value') and s.get('estimated_value') >= min_value]
        
        if max_value > 0:
            filtered_history = [s for s in filtered_history 
                              if s.get('estimated_value') and s.get('estimated_value') <= max_value]
        
        # Apply sorting
        if sort_by == "Search Date (Newest)":
            filtered_history.sort(key=lambda x: x['search_date'], reverse=True)
        elif sort_by == "Search Date (Oldest)":
            filtered_history.sort(key=lambda x: x['search_date'])
        elif sort_by == "Property Value (High to Low)":
            filtered_history.sort(key=lambda x: x.get('estimated_value', 0), reverse=True)
        elif sort_by == "Property Value (Low to High)":
            filtered_history.sort(key=lambda x: x.get('estimated_value', 0))
        elif sort_by == "Address (A-Z)":
            filtered_history.sort(key=lambda x: x.get('property_address', ''))
        elif sort_by == "Property Type":
            filtered_history.sort(key=lambda x: x.get('property_type', ''))

        # Display filter results
        total_results = len(filtered_history)
        st.markdown(f"**Found {total_results} searches** (filtered from {len(search_history)} total)")
        
        # Bulk actions
        if filtered_history:
            bulk_col1, bulk_col2, bulk_col3, bulk_col4 = st.columns(4)
            
            with bulk_col1:
                if st.button("📤 Export Filtered", help="Export filtered results"):
                    if total_results > 0:
                        export_data = json.dumps(filtered_history, indent=2, default=str)
                        st.download_button(
                            label="⬇️ Download JSON",
                            data=export_data,
                            file_name=f"filtered_searches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    else:
                        st.warning("No data to export")
            
            with bulk_col2:
                if st.button("🗑️ Delete Filtered", help="Delete all filtered searches"):
                    if st.session_state.get('confirm_bulk_delete'):
                        search_ids = [s['id'] for s in filtered_history]
                        success, deleted_count = bulk_delete_property_searches(user_id, search_ids)
                        if success:
                            st.success(f"✅ Deleted {deleted_count} searches!")
                            st.rerun()
                        else:
                            st.error("❌ Error deleting searches")
                        st.session_state.confirm_bulk_delete = False
                    else:
                        st.session_state.confirm_bulk_delete = True
                        st.warning(f"⚠️ Click again to confirm deleting {total_results} searches")
            
            with bulk_col3:
                if st.button("🗑️ Clear All History", help="Delete all search history"):
                    if st.session_state.get('confirm_clear_all'):
                        success, deleted_count = bulk_delete_property_searches(user_id)
                        if success:
                            st.success(f"✅ Cleared all {deleted_count} searches!")
                            st.rerun()
                        else:
                            st.error("❌ Error clearing history")
                        st.session_state.confirm_clear_all = False
                    else:
                        st.session_state.confirm_clear_all = True
                        st.warning("⚠️ Click again to confirm clearing ALL history")
            
            with bulk_col4:
                if st.button("🔄 Refresh History", help="Reload search history"):
                    st.rerun()

        # Pagination for large result sets
        items_per_page = 10
        total_pages = (total_results + items_per_page - 1) // items_per_page
        
        if total_pages > 1:
            page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
            with page_col2:
                current_page = st.selectbox("📄 Page", range(1, total_pages + 1), key="history_page")
            
            start_idx = (current_page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, total_results)
            displayed_history = filtered_history[start_idx:end_idx]
            
            st.markdown(f"Showing items {start_idx + 1}-{end_idx} of {total_results}")
        else:
            displayed_history = filtered_history

        # Display search history with enhanced cards
        for i, search in enumerate(displayed_history):
            property_data = search['property_data']
            search_date = datetime.fromisoformat(search['search_date'].replace('Z', '+00:00'))
            formatted_date = search_date.strftime("%B %d, %Y at %I:%M %p")
            address = safe_get(property_data, 'formattedAddress', safe_get(property_data, 'address', 'Unknown Address'))
            
            # Create expandable card with rich preview
            with st.expander(f"🏠 {address} - {formatted_date}", expanded=False):
                # Main content columns
                main_col1, main_col2, main_col3 = st.columns([2, 2, 1])
                
                with main_col1:
                    # Property summary
                    property_type = safe_get(property_data, 'propertyType')
                    bedrooms = safe_get(property_data, 'bedrooms')
                    bathrooms = safe_get(property_data, 'bathrooms')
                    estimated_value = safe_get(property_data, 'estimatedValue')
                    year_built = safe_get(property_data, 'yearBuilt')
                    
                    st.markdown(f"""
                    **🏠 Property:** {property_type}  
                    **🛏️ Bedrooms:** {bedrooms} | **🚿 Bathrooms:** {bathrooms}  
                    **📅 Built:** {year_built} | **📏 Size:** {format_area(safe_get(property_data, 'squareFootage'))}
                    """)
                
                with main_col2:
                    # Financial information
                    data_completeness = search.get('data_completeness_score', 0) * 100
                    
                    st.markdown(f"""
                    **💰 Estimated Value:** {format_currency(estimated_value)}  
                    **📊 Data Quality:** {data_completeness:.1f}%  
                    **🔍 Search Query:** {search.get('search_query', 'N/A')}
                    """)
                
                with main_col3:
                    # Action buttons
                    if st.button(f"🗑️ Delete", key=f"delete_{search['id']}", help="Delete this search"):
                        if delete_property_search(search['id'], user_id):
                            st.success("✅ Search deleted!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete")
                    
                    if st.button(f"📄 Export", key=f"export_{search['id']}", help="Export this search"):
                        json_data = json.dumps(property_data, indent=2, default=str)
                        st.download_button(
                            label="⬇️ JSON",
                            data=json_data,
                            file_name=f"property_{address.replace(' ', '_')}_{search['id']}.json",
                            mime="application/json",
                            key=f"download_{search['id']}"
                        )

                # Detailed view toggle
                detail_key = f"show_details_{search['id']}"
                if st.button(f"👁️ {'Hide' if st.session_state.get(detail_key, False) else 'Show'} Details", 
                           key=f"toggle_{search['id']}"):
                    st.session_state[detail_key] = not st.session_state.get(detail_key, False)
                    st.rerun()
                
                # Show detailed property information if toggled
                if st.session_state.get(detail_key, False):
                    st.markdown("---")
                    
                    # Render comprehensive property cards in compact mode
                    cards_html = render_comprehensive_property_cards(property_data, compact=True)
                    
                    if cards_html:
                        compact_html = f"""
                        <style>
                            .compact-container {{
                                display: grid;
                                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                                gap: 16px;
                                padding: 12px 0;
                            }}
                            .compact-card {{
                                background: linear-gradient(145deg, #f8f9fa, #e9ecef);
                                padding: 18px;
                                border-radius: 12px;
                                border: 1px solid #dee2e6;
                                transition: transform 0.2s ease;
                            }}
                            .compact-card:hover {{
                                transform: translateY(-2px);
                                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                            }}
                            .compact-card h4 {{
                                margin-top: 0;
                                margin-bottom: 14px;
                                color: #495057;
                                font-size: 17px;
                                font-weight: 600;
                                border-bottom: 2px solid #adb5bd;
                                padding-bottom: 8px;
                                display: flex;
                                align-items: center;
                                gap: 6px;
                            }}
                            .compact-content {{
                                font-size: 14px;
                                line-height: 1.7;
                                color: #6c757d;
                            }}
                            .compact-content b {{
                                color: #495057;
                                font-weight: 600;
                            }}
                            .compact-content pre {{
                                font-size: 11px;
                                max-height: 300px;
                                overflow-y: auto;
                                background: #ffffff;
                                border: 1px solid #ced4da;
                            }}
                        </style>
                        <div class="compact-container">
                            {cards_html}
                        </div>
                        """
                        html(compact_html, height=600, scrolling=True)
                    
                    # Additional actions for detailed view
                    st.markdown("---")
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if st.button(f"🔄 Re-search Property", key=f"research_{search['id']}", help="Search for updated data"):
                            st.info(f"💡 Go to the 'Property Search' tab and search for: **{address}**")
                    
                    with action_col2:
                        if st.button(f"📋 Copy Address", key=f"copy_{search['id']}", help="Copy address to clipboard"):
                            st.code(address, language=None)
                            st.success("📋 Address ready to copy!")
                    
                    with action_col3:
                        if st.button(f"⭐ Add to Favorites", key=f"favorite_{search['id']}", help="Add to favorites"):
                            st.info("⭐ Favorites feature coming soon!")

# =====================================================
# 10. ANALYTICS DASHBOARD TAB
# =====================================================
with tab3:
    st.title("📊 Property Search Analytics")
    st.markdown("Comprehensive analytics and insights from your property search history.")
    
    stats = get_enhanced_search_statistics(user_id)
    
    if not stats or stats.get('total_searches', 0) == 0:
        st.info("📈 Analytics will appear here once you start searching for properties!")
    else:
        # Overview metrics
        st.subheader("📈 Search Overview")
        
        overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
        
        with overview_col1:
            st.metric("Total Searches", stats.get('total_searches', 0))
        with overview_col2:
            st.metric("Recent Searches", stats.get('recent_searches', 0))
        with overview_col3:
            st.metric("Avg Data Quality", f"{stats.get('average_data_completeness', 0)}%")
        with overview_col4:
            trend = stats.get('search_trends', {}).get('trend', 'stable')
            st.metric("Search Trend", trend.title())
        
        # Charts and visualizations
        if stats.get('top_property_types'):
            st.subheader("🏠 Property Type Distribution")
            
            prop_types_data = dict(stats['top_property_types'])
            if len(prop_types_data) > 0:
                # Create a simple bar chart using Streamlit
                st.bar_chart(prop_types_data)
        
        # Value analysis
        if stats.get('value_statistics'):
            st.subheader("💰 Property Value Analysis")
            value_stats = stats['value_statistics']
            
            value_col1, value_col2, value_col3, value_col4 = st.columns(4)
            with value_col1:
                st.metric("Minimum Value", format_currency(value_stats.get('min_value', 0)))
            with value_col2:
                st.metric("Maximum Value", format_currency(value_stats.get('max_value', 0)))
            with value_col3:
                st.metric("Average Value", format_currency(value_stats.get('avg_value', 0)))
            with value_col4:
                st.metric("Median Value", format_currency(value_stats.get('median_value', 0)))
        
        # Geographic distribution
        if stats.get('top_cities'):
            st.subheader("🌆 Geographic Distribution")
            
            cities_data = dict(stats['top_cities'][:10])  # Top 10 cities
            if len(cities_data) > 0:
                st.bar_chart(cities_data)
        
        # Search trends over time
        if stats.get('search_trends', {}).get('monthly_distribution'):
            st.subheader("📅 Search Activity Over Time")
            
            monthly_data = stats['search_trends']['monthly_distribution']
            if len(monthly_data) > 0:
                # Convert to a format suitable for line chart
                df_monthly = pd.DataFrame(list(monthly_data.items()), columns=['Month', 'Searches'])
                st.line_chart(df_monthly.set_index('Month'))
        
        # Data quality metrics
        if stats.get('data_quality_metrics'):
            st.subheader("📊 Data Quality Metrics")
            
            quality_metrics = stats['data_quality_metrics']
            
            quality_col1, quality_col2 = st.columns(2)
            
            with quality_col1:
                st.metric("Owner Info Coverage", f"{quality_metrics.get('owner_info_coverage', 0)}%")
                st.metric("Transaction History Coverage", f"{quality_metrics.get('history_coverage', 0)}%")
            
            with quality_col2:
                st.metric("Tax Data Coverage", f"{quality_metrics.get('tax_data_coverage', 0)}%")
                st.metric("Market Data Coverage", f"{quality_metrics.get('market_data_coverage', 0)}%")
        
        # Bedroom distribution
        if stats.get('bedroom_distribution'):
            st.subheader("🛏️ Bedroom Distribution")
            
            bedroom_data = stats['bedroom_distribution']
            if len(bedroom_data) > 0:
                # Sort by bedroom count
                sorted_bedrooms = dict(sorted(bedroom_data.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0))
                st.bar_chart(sorted_bedrooms)
        
        # Export analytics
        st.subheader("📤 Export Analytics")
        
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            if st.button("📊 Export Analytics Report"):
                analytics_report = {
                    'generated_date': datetime.now().isoformat(),
                    'user_id': user_id,
                    'analytics_data': stats
                }
                
                report_json = json.dumps(analytics_report, indent=2, default=str)
                st.download_button(
                    label="⬇️ Download Analytics JSON",
                    data=report_json,
                    file_name=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with export_col2:
            if st.button("📈 Generate Summary Report"):
                st.info("📋 Detailed summary report generation coming soon!")

# =====================================================
# 11. Debug Mode (Enhanced)
# =====================================================
if st.sidebar.checkbox("🔧 Debug Mode", help="Show comprehensive debugging information"):
    with st.sidebar:
        st.subheader("🔧 Debug Information")
        
        debug_info = {
            "user_id": user_id,
            "user_email": user_email,
            "queries_used": queries_used,
            "session_state_keys": list(st.session_state.keys()),
            "supabase_connected": bool(supabase),
            "current_time": datetime.now().isoformat()
        }
        
        if 'search_history' in locals():
            debug_info["total_searches_loaded"] = len(search_history)
        
        if 'stats' in locals() and stats:
            debug_info["analytics_available"] = True
            debug_info["stats_keys"] = list(stats.keys())
        
        st.json(debug_info)
        
        # Additional debug actions
        if st.button("🔄 Clear Session State"):
            for key in list(st.session_state.keys()):
                if key.startswith(('show_details_', 'confirm_')):
                    del st.session_state[key]
            st.success("🧹 Session state cleared!")
            st.rerun()
        
        if st.button("📊 Test Database Connection"):
            try:
                test_result = supabase.table('property_searches').select('id').limit(1).execute()
                st.success("✅ Database connection successful!")
                st.json({"connection_test": "passed", "result_count": len(test_result.data)})
            except Exception as e:
                st.error(f"❌ Database connection failed: {str(e)}")

# =====================================================
# 12. Footer
# =====================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d; font-size: 12px; padding: 20px;'>
    <p>🏠 Advanced Property Search System | Built with Streamlit & Supabase</p>
    <p>💡 All searches are automatically saved and can be exported at any time</p>
</div>
""", unsafe_allow_html=True)
