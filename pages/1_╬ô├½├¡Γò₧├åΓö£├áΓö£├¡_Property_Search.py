# =====================================================
# pages/1_🏠_Property_Search.py
# =====================================================

import streamlit as st
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from utils.auth import initialize_auth_state
from utils.rentcast_api import fetch_property_details
from utils.database import get_user_usage
from streamlit.components.v1 import html
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Property Search", page_icon="🏠", layout="wide")

# =====================================================
# 1. Database Connection & Functions
# =====================================================

def get_db_connection():
    """Get database connection using Supabase credentials"""
    try:
        # Replace these with your actual Supabase database credentials
        conn = psycopg2.connect(
            host=os.getenv("SUPABASE_DB_HOST"),
            database=os.getenv("SUPABASE_DB_NAME"),
            user=os.getenv("SUPABASE_DB_USER"),
            password=os.getenv("SUPABASE_DB_PASSWORD"),
            port=os.getenv("SUPABASE_DB_PORT", "5432")
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def save_property_search(user_id: str, property_data: Dict[Any, Any]) -> bool:
    """Save property search to database"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO property_searches (user_id, property_data, search_date)
                VALUES (%s, %s, %s)
            """, (user_id, json.dumps(property_data), datetime.now()))
            conn.commit()
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving property search: {e}")
        return False

def get_user_property_searches(user_id: str, limit: int = 50) -> List[Dict]:
    """Get user's property search history"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
            
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, property_data, search_date
                FROM property_searches 
                WHERE user_id = %s 
                ORDER BY search_date DESC 
                LIMIT %s
            """, (user_id, limit))
            results = cur.fetchall()
        
        conn.close()
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error fetching property searches: {e}")
        return []

def delete_property_search(search_id: int, user_id: str) -> bool:
    """Delete a specific property search"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM property_searches 
                WHERE id = %s AND user_id = %s
            """, (search_id, user_id))
            conn.commit()
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error deleting property search: {e}")
        return False

def get_search_statistics(user_id: str) -> Dict[str, Any]:
    """Get user's search statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return {}
            
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Total searches
            cur.execute("SELECT COUNT(*) as total FROM property_searches WHERE user_id = %s", (user_id,))
            total_searches = cur.fetchone()['total']
            
            # Recent searches (last 30 days)
            cur.execute("""
                SELECT COUNT(*) as recent 
                FROM property_searches 
                WHERE user_id = %s AND search_date >= %s
            """, (user_id, datetime.now() - timedelta(days=30)))
            recent_searches = cur.fetchone()['recent']
            
            # Most searched property types
            cur.execute("""
                SELECT 
                    property_data->>'propertyType' as property_type,
                    COUNT(*) as count
                FROM property_searches 
                WHERE user_id = %s 
                    AND property_data->>'propertyType' IS NOT NULL
                GROUP BY property_data->>'propertyType'
                ORDER BY count DESC
                LIMIT 5
            """, (user_id,))
            property_types = cur.fetchall()
        
        conn.close()
        return {
            'total_searches': total_searches,
            'recent_searches': recent_searches,
            'top_property_types': [dict(row) for row in property_types]
        }
    except Exception as e:
        logger.error(f"Error getting search statistics: {e}")
        return {}

# =====================================================
# 2. Initialize & Auth
# =====================================================
initialize_auth_state()

if st.session_state.user is None:
    st.warning("⚠️ Please log in from the main page to access this feature.")
    st.stop()

user_email = st.session_state.user.email
user_id = st.session_state.user.id

# =====================================================
# 3. Sidebar (Usage / Limits & Quick Stats)
# =====================================================
with st.sidebar:
    st.subheader("👤 Account Info")
    queries_used = get_user_usage(user_id, user_email)
    
    st.metric("Email", user_email)
    st.metric("Queries Used", f"{queries_used}/30")
    
    if queries_used >= 30:
        st.error("🚫 Query limit reached!")
    elif queries_used >= 25:
        st.warning("⚠️ Approaching limit!")
    
    # Search Statistics
    st.subheader("📊 Search Statistics")
    stats = get_search_statistics(user_id)
    if stats:
        st.metric("Total Searches", stats.get('total_searches', 0))
        st.metric("Last 30 Days", stats.get('recent_searches', 0))
        
        if stats.get('top_property_types'):
            st.subheader("🏠 Top Property Types")
            for prop_type in stats['top_property_types']:
                st.text(f"{prop_type['property_type']}: {prop_type['count']}")

# =====================================================
# 4. Tab Layout
# =====================================================
tab1, tab2 = st.tabs(["🔍 New Search", "📚 Search History"])

# =====================================================
# 5. Helper Functions (Moved from original)
# =====================================================
def safe_get(data, key, default="N/A"):
    """Safely get a value from dict with default fallback"""
    try:
        value = data.get(key, default)
        return value if value is not None and value != "" else default
    except (AttributeError, TypeError):
        return default

def format_currency(value):
    """Format currency values safely"""
    try:
        if isinstance(value, (int, float)) and value > 0:
            return f"${value:,.0f}"
        elif isinstance(value, str) and value.replace(',', '').replace('$', '').isdigit():
            return f"${int(value.replace(',', '').replace('$', '')):,}"
        return "N/A"
    except (ValueError, TypeError):
        return "N/A"

def build_card(title: str, content: str) -> str:
    """Build HTML card component"""
    return f"""
    <div class="card">
        <h3>{title}</h3>
        <div class="content">{content}</div>
    </div>
    """

def build_compact_card(title: str, content: str, card_id: str = "") -> str:
    """Build compact HTML card for history view"""
    return f"""
    <div class="compact-card" id="{card_id}">
        <h4>{title}</h4>
        <div class="compact-content">{content}</div>
    </div>
    """

def process_property_data(raw_data):
    """Process and validate property data from API response"""
    try:
        logger.info(f"Raw API response type: {type(raw_data)}")
        logger.info(f"Raw API response: {str(raw_data)[:500]}...")
        
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
            
        properties = None
        
        if isinstance(property_data, list) and len(property_data) > 0:
            properties = property_data
        elif isinstance(property_data, dict) and "properties" in property_data:
            properties = property_data["properties"]
        elif isinstance(property_data, dict) and "data" in property_data:
            properties = property_data["data"]
        elif isinstance(property_data, dict) and any(key in property_data for key in ["formattedAddress", "propertyType", "bedrooms", "id"]):
            properties = [property_data]
        
        if not properties or len(properties) == 0:
            logger.error("No properties found in response")
            return None
            
        first_property = properties[0]
        logger.info(f"Successfully processed property: {first_property.get('formattedAddress', 'Unknown Address')}")
        return first_property
        
    except Exception as e:
        logger.error(f"Error processing property data: {e}")
        return None

def render_property_cards(prop: Dict[Any, Any], compact: bool = False) -> str:
    """Render property information as HTML cards"""
    cards_html = ""
    card_function = build_compact_card if compact else build_card
    
    # Basic Property Information
    basic_info = f"""
    <b>Property Type:</b> {safe_get(prop, 'propertyType')}<br>
    <b>Bedrooms:</b> {safe_get(prop, 'bedrooms')}<br>
    <b>Bathrooms:</b> {safe_get(prop, 'bathrooms')}<br>
    <b>Square Footage:</b> {safe_get(prop, 'squareFootage')} sq ft<br>
    <b>Year Built:</b> {safe_get(prop, 'yearBuilt')}
    """
    cards_html += card_function("🏠 Basic Information", basic_info)

    # Address Information
    address_info = f"""
    <b>Full Address:</b> {safe_get(prop, 'formattedAddress', safe_get(prop, 'address'))}<br>
    <b>City:</b> {safe_get(prop, 'city')}<br>
    <b>State:</b> {safe_get(prop, 'state')}<br>
    <b>ZIP Code:</b> {safe_get(prop, 'zipCode')}
    """
    cards_html += card_function("📍 Address", address_info)

    # Valuation Information
    valuation_info = ""
    estimated_value = safe_get(prop, 'estimatedValue')
    if estimated_value != "N/A":
        valuation_info += f"<b>Estimated Value:</b> {format_currency(estimated_value)}<br>"
    
    market_value = safe_get(prop, 'marketValue')
    if market_value != "N/A":
        valuation_info += f"<b>Market Value:</b> {format_currency(market_value)}<br>"
    
    if valuation_info:
        cards_html += card_function("💰 Property Valuation", valuation_info)

    if not compact:
        # Additional detailed information for full view
        
        # Features & Amenities
        features = safe_get(prop, 'features')
        if features != "N/A" and isinstance(features, dict):
            features_html = "<br>".join([
                f"<b>{k.replace('_', ' ').title()}:</b> {v}" 
                for k, v in features.items() if v
            ])
            if features_html:
                cards_html += card_function("🔧 Features & Amenities", features_html)

        # Property Taxes
        property_taxes = safe_get(prop, 'propertyTaxes')
        if property_taxes != "N/A" and isinstance(property_taxes, dict):
            tax_html = ""
            for year, tax_data in property_taxes.items():
                if isinstance(tax_data, dict):
                    total = format_currency(tax_data.get('total', 0))
                    tax_html += f"<b>{year}:</b> {total}<br>"
                else:
                    tax_html += f"<b>{year}:</b> {format_currency(tax_data)}<br>"
            
            if tax_html:
                cards_html += card_function("🏛️ Property Taxes", tax_html)

        # Sale History
        history = safe_get(prop, 'history')
        if history != "N/A" and isinstance(history, (dict, list)):
            hist_html = ""
            if isinstance(history, dict):
                for event_key, event_data in history.items():
                    if isinstance(event_data, dict):
                        event_type = event_data.get('event', 'Sale')
                        date = event_data.get('date', 'Unknown')
                        price = format_currency(event_data.get('price', 0))
                        hist_html += f"<b>{event_type}:</b> {date} - {price}<br>"
            elif isinstance(history, list):
                for event in history:
                    if isinstance(event, dict):
                        event_type = event.get('event', 'Sale')
                        date = event.get('date', 'Unknown')
                        price = format_currency(event.get('price', 0))
                        hist_html += f"<b>{event_type}:</b> {date} - {price}<br>"
            
            if hist_html:
                cards_html += card_function("📜 Sale History", hist_html)

        # Owner Information
        owner = safe_get(prop, 'owner')
        if owner != "N/A" and isinstance(owner, dict):
            owner_html = ""
            names = owner.get('names', [])
            if names:
                owner_html += f"<b>Owner(s):</b> {', '.join(names)}<br>"
            
            if owner_html:
                cards_html += card_function("👤 Owner Information", owner_html)

    return cards_html

# =====================================================
# 6. NEW SEARCH TAB
# =====================================================
with tab1:
    st.title("🏠 Property Search")
    st.markdown("Retrieve detailed property information with a clean, card-based layout.")

    address = st.text_input(
        "Enter Property Address",
        placeholder="e.g., 123 Main St, New York, NY 10001",
        help="Enter a complete address for best results"
    )

    if st.button("🔍 Search Property", type="primary", use_container_width=True):
        if not address:
            st.error("❌ Please enter a property address.")
        else:
            with st.spinner("🔎 Fetching property data..."):
                try:
                    # Fetch raw data from API
                    raw_response = fetch_property_details(address, user_id, user_email)
                    
                    if not raw_response:
                        st.error("⚠️ No response from API. Please try again.")
                        st.stop()
                    
                    # Process the response
                    prop = process_property_data(raw_response)
                    
                    if not prop:
                        st.error("⚠️ No property data found or invalid response format.")
                        with st.expander("Debug: Raw API Response"):
                            st.code(str(raw_response)[:2000] + "..." if len(str(raw_response)) > 2000 else str(raw_response))
                        st.stop()

                    # Display success message
                    property_address = safe_get(prop, 'formattedAddress', safe_get(prop, 'address', address))
                    st.success(f"✅ Property found: {property_address}")

                    # Save to database
                    if save_property_search(user_id, prop):
                        st.success("💾 Search saved to history!")
                    else:
                        st.warning("⚠️ Could not save search to history (search still completed)")

                    # Build and render property cards
                    cards_html = render_property_cards(prop, compact=False)
                    
                    # Add raw JSON data for debugging
                    try:
                        pretty_json = json.dumps(prop, indent=2, default=str)
                        if len(pretty_json) > 5000:
                            pretty_json = pretty_json[:5000] + "\n\n... (truncated)"
                        cards_html += build_card("📋 Raw JSON Data", f"<pre>{pretty_json}</pre>")
                    except Exception as e:
                        cards_html += build_card("📋 Raw JSON Data", f"<pre>Error displaying JSON: {str(e)}</pre>")

                    if not cards_html:
                        st.warning("⚠️ No property information could be extracted from the response.")
                    else:
                        # Render final layout
                        full_html = f"""
                        <style>
                            body {{
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                color: #2c3e50;
                                background-color: #f8f9fa;
                            }}
                            .container {{
                                display: grid;
                                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                                gap: 20px;
                                padding: 10px;
                            }}
                            .card {{
                                background: #ffffff;
                                padding: 24px;
                                border-radius: 12px;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                                transition: all 0.3s ease;
                                border: 1px solid #e9ecef;
                            }}
                            .card:hover {{
                                transform: translateY(-2px);
                                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                            }}
                            .card h3 {{
                                margin-top: 0;
                                margin-bottom: 16px;
                                color: #2c3e50;
                                font-size: 20px;
                                font-weight: 600;
                                border-bottom: 2px solid #3498db;
                                padding-bottom: 8px;
                            }}
                            .content {{
                                font-size: 14px;
                                line-height: 1.8;
                                color: #495057;
                            }}
                            .content b {{
                                color: #2c3e50;
                                font-weight: 600;
                            }}
                            pre {{
                                white-space: pre-wrap;
                                word-wrap: break-word;
                                background: #f8f9fa;
                                padding: 16px;
                                border-radius: 8px;
                                font-size: 12px;
                                border: 1px solid #dee2e6;
                                max-height: 400px;
                                overflow-y: auto;
                            }}
                            @media (max-width: 768px) {{
                                .container {{
                                    grid-template-columns: 1fr;
                                }}
                            }}
                        </style>
                        <div class="container">
                            {cards_html}
                        </div>
                        """
                        html(full_html, height=1200, scrolling=True)

                except Exception as e:
                    logger.error(f"Error in property search: {e}")
                    st.error(f"❌ Error fetching property data: {str(e)}")
                    
                    with st.expander("🔍 Debug Information"):
                        st.text(f"Error Type: {type(e).__name__}")
                        st.text(f"Error Message: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

    # Tips section
    st.markdown("---")
    st.subheader("💡 Tips for Better Results")
    st.markdown("""
    - Include the **full address** with city, state, and ZIP code  
    - Use standard address formatting (e.g., `123 Main St, New York, NY 10001`)  
    - Double-check spelling of **street/city names**  
    - For apartments/condos, include **unit numbers** if possible  
    - If no results are found, try variations of the address format
    - All successful searches are automatically saved to your history
    """)

# =====================================================
# 7. SEARCH HISTORY TAB
# =====================================================
with tab2:
    st.title("📚 Property Search History")
    st.markdown("View and manage all your past property searches.")

    # Fetch search history
    search_history = get_user_property_searches(user_id)
    
    if not search_history:
        st.info("📭 No search history found. Start searching for properties to build your history!")
    else:
        # Search filters
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            search_filter = st.text_input("🔍 Filter by address", placeholder="Type to filter...")
        
        with col2:
            date_filter = st.selectbox(
                "📅 Filter by date",
                ["All time", "Last 7 days", "Last 30 days", "Last 90 days"]
            )
        
        with col3:
            if st.button("🗑️ Clear All History", type="secondary"):
                if st.session_state.get('confirm_clear_history'):
                    # Clear all history
                    try:
                        conn = get_db_connection()
                        if conn:
                            with conn.cursor() as cur:
                                cur.execute("DELETE FROM property_searches WHERE user_id = %s", (user_id,))
                                conn.commit()
                            conn.close()
                            st.success("✅ Search history cleared!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error clearing history: {e}")
                    
                    st.session_state.confirm_clear_history = False
                else:
                    st.session_state.confirm_clear_history = True
                    st.warning("⚠️ Click again to confirm clearing all history")

        # Apply filters
        filtered_history = search_history.copy()
        
        # Date filter
        if date_filter != "All time":
            days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
            cutoff_date = datetime.now() - timedelta(days=days_map[date_filter])
            filtered_history = [
                search for search in filtered_history 
                if search['search_date'] >= cutoff_date
            ]
        
        # Address filter
        if search_filter:
            filtered_history = [
                search for search in filtered_history
                if search_filter.lower() in json.dumps(search['property_data']).lower()
            ]

        st.markdown(f"**Found {len(filtered_history)} searches**")
        
        # Display search history
        for i, search in enumerate(filtered_history):
            property_data = search['property_data']
            search_date = search['search_date'].strftime("%B %d, %Y at %I:%M %p")
            address = safe_get(property_data, 'formattedAddress', safe_get(property_data, 'address', 'Unknown Address'))
            
            with st.expander(f"🏠 {address} - {search_date}", expanded=False):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Quick summary
                    property_type = safe_get(property_data, 'propertyType')
                    bedrooms = safe_get(property_data, 'bedrooms')
                    bathrooms = safe_get(property_data, 'bathrooms')
                    estimated_value = safe_get(property_data, 'estimatedValue')
                    
                    st.markdown(f"""
                    **Property Type:** {property_type}  
                    **Bedrooms:** {bedrooms} | **Bathrooms:** {bathrooms}  
                    **Estimated Value:** {format_currency(estimated_value)}  
                    **Search Date:** {search_date}
                    """)
                
                with col2:
                    if st.button(f"🗑️ Delete", key=f"delete_{search['id']}"):
                        if delete_property_search(search['id'], user_id):
                            st.success("✅ Search deleted!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete search")

                # Show detailed view toggle
                if st.button(f"👁️ View Details", key=f"view_{search['id']}"):
                    st.session_state[f"show_details_{search['id']}"] = not st.session_state.get(f"show_details_{search['id']}", False)
                
                # Show detailed property information if toggled
                if st.session_state.get(f"show_details_{search['id']}", False):
                    st.markdown("---")
                    
                    # Render property cards in compact mode
                    cards_html = render_property_cards(property_data, compact=True)
                    
                    if cards_html:
                        compact_html = f"""
                        <style>
                            .compact-container {{
                                display: grid;
                                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                                gap: 15px;
                                padding: 10px 0;
                            }}
                            .compact-card {{
                                background: #f8f9fa;
                                padding: 16px;
                                border-radius: 8px;
                                border: 1px solid #dee2e6;
                            }}
                            .compact-card h4 {{
                                margin-top: 0;
                                margin-bottom: 12px;
                                color: #495057;
                                font-size: 16px;
                                font-weight: 600;
                                border-bottom: 1px solid #adb5bd;
                                padding-bottom: 6px;
                            }}
                            .compact-content {{
                                font-size: 13px;
                                line-height: 1.6;
                                color: #6c757d;
                            }}
                            .compact-content b {{
                                color: #495057;
                                font-weight: 600;
                            }}
                        </style>
                        <div class="compact-container">
                            {cards_html}
                        </div>
                        """
                        html(compact_html, height=400, scrolling=True)
                    
                    # Export options
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"📄 Export as JSON", key=f"export_json_{search['id']}"):
                            st.download_button(
                                label="⬇️ Download JSON",
                                data=json.dumps(property_data, indent=2, default=str),
                                file_name=f"property_{address.replace(' ', '_').replace(',', '')}_{search_date.replace(' ', '_').replace(':', '')}.json",
                                mime="application/json",
                                key=f"download_json_{search['id']}"
                            )
                    
                    with col2:
                        # Re-search button (to get updated data)
                        if st.button(f"🔄 Re-search Property", key=f"research_{search['id']}"):
                            st.info(f"💡 Go to the 'New Search' tab and search for: {address}")

# =====================================================
# 8. Debug Mode (Optional)
# =====================================================
if st.sidebar.checkbox("🔧 Debug Mode", help="Show additional debugging information"):
    with st.sidebar:
        st.subheader("🔧 Debug Information")
        st.json({
            "user_id": user_id,
            "user_email": user_email,
            "queries_used": queries_used,
            "total_searches": len(search_history) if 'search_history' in locals() else 0
        })
