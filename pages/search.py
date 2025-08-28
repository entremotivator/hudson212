# =====================================================
# pages/1_🏠_Property_Search.py
# =====================================================

import streamlit as st
import json
import pandas as pd
from utils.auth import initialize_auth_state
from utils.rentcast_api import fetch_property_details, get_market_data
from utils.database import get_user_usage

st.set_page_config(page_title="Property Search", page_icon="🏠")

# Initialize auth state
initialize_auth_state()

# Check if user is authenticated
if st.session_state.user is None:
    st.warning("Please log in from the main page to access this feature.")
    st.stop()

st.title("🏠 Property Search")
st.markdown("Search for detailed property information and market analytics.")

# User info sidebar
with st.sidebar:
    st.subheader("Account Info")
    user_email = st.session_state.user.email
    user_id = st.session_state.user.id
    
    # Safe database call with error handling
    try:
        queries_used = get_user_usage(user_id, user_email)
    except Exception as e:
        st.warning("⚠️ Unable to load usage data")
        queries_used = 0  # Default to 0 if database error
    
    st.metric("Email", user_email)
    st.metric("Queries Used", f"{queries_used}/30")
    
    if queries_used >= 30:
        st.error("🚫 Query limit reached!")
    elif queries_used >= 25:
        st.warning("⚠️ Approaching limit!")

# Helper function to format currency
def format_currency(value):
    if value is None or value == "N/A":
        return "N/A"
    try:
        return f"${int(value):,}"
    except (ValueError, TypeError):
        return str(value)

# Helper function to format date
def format_date(date_str):
    if date_str is None:
        return "N/A"
    try:
        from datetime import datetime
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y")
    except:
        return str(date_str)

# Helper function to safely get nested values
def safe_get(data, keys, default="N/A"):
    """Safely get nested dictionary values"""
    try:
        for key in keys:
            data = data[key]
        return data if data is not None else default
    except (KeyError, TypeError, IndexError):
        return default

# Main content
st.subheader("🔍 Search Property")
address = st.text_input(
    "Enter Property Address",
    placeholder="e.g., 123 Main St, New York, NY 10001",
    help="Enter a complete address for best results"
)

if st.button("🔍 Search Property", type="primary", use_container_width=True):
    if not address:
        st.error("Please enter a property address.")
    else:
        # Check query limit before making API call
        if queries_used >= 30:
            st.error("❌ You have reached your query limit of 30 searches. Please contact support to increase your limit.")
        else:
            with st.spinner("Searching property data..."):
                try:
                    # Fetch property details (returns JSON array format)
                    property_data = fetch_property_details(address, user_id, user_email)
                    
                    if property_data and len(property_data) > 0:
                st.success("✅ Property data retrieved successfully!")
                
                # Get the first property from the array
                prop = property_data[0]
                
                # Display property information in organized tabs
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🏠 Basic Info", 
                    "🏗️ Property Details", 
                    "💰 Financial Data", 
                    "👤 Owner Info", 
                    "📋 Raw JSON"
                ])
                
                with tab1:
                    st.markdown("### 🏠 Basic Property Information")
                    
                    # Address Card
                    with st.container():
                        st.markdown("**📍 Address Information**")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Address", prop.get("formattedAddress", "N/A"))
                            st.metric("City", prop.get("city", "N/A"))
                        
                        with col2:
                            st.metric("State", prop.get("state", "N/A"))
                            st.metric("ZIP Code", prop.get("zipCode", "N/A"))
                        
                        with col3:
                            st.metric("County", prop.get("county", "N/A"))
                            st.metric("County FIPS", prop.get("countyFips", "N/A"))
                        
                        st.markdown("---")
                    
                    # Basic Property Stats
                    with st.container():
                        st.markdown("**🏠 Property Specifications**")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Property Type", prop.get("propertyType", "N/A"))
                            st.metric("Bedrooms", prop.get("bedrooms", "N/A"))
                        
                        with col2:
                            st.metric("Bathrooms", prop.get("bathrooms", "N/A"))
                            st.metric("Square Footage", f"{prop.get('squareFootage', 'N/A'):,}" if prop.get('squareFootage') else "N/A")
                        
                        with col3:
                            st.metric("Lot Size", f"{prop.get('lotSize', 'N/A'):,} sq ft" if prop.get('lotSize') else "N/A")
                            st.metric("Year Built", prop.get("yearBuilt", "N/A"))
                        
                        with col4:
                            st.metric("Assessor ID", prop.get("assessorID", "N/A"))
                            st.metric("Zoning", prop.get("zoning", "N/A"))
                
                with tab2:
                    st.markdown("### 🏗️ Detailed Property Features")
                    
                    # Features Card
                    if "features" in prop and prop["features"]:
                        features = prop["features"]
                        
                        with st.container():
                            st.markdown("**🏗️ Architectural Features**")
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Architecture", features.get("architectureType", "N/A"))
                                st.metric("Exterior", features.get("exteriorType", "N/A"))
                                st.metric("Roof Type", features.get("roofType", "N/A"))
                            
                            with col2:
                                st.metric("Foundation", features.get("foundationType", "N/A"))
                                st.metric("Floor Count", features.get("floorCount", "N/A"))
                                st.metric("Room Count", features.get("roomCount", "N/A"))
                            
                            with col3:
                                st.metric("Unit Count", features.get("unitCount", "N/A"))
                                st.metric("Fireplace", "Yes" if features.get("fireplace") else "No")
                                st.metric("Fireplace Type", features.get("fireplaceType", "N/A"))
                            
                            st.markdown("---")
                        
                        with st.container():
                            st.markdown("**🌡️ Climate & Utilities**")
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Heating", "Yes" if features.get("heating") else "No")
                                st.metric("Heating Type", features.get("heatingType", "N/A"))
                            
                            with col2:
                                st.metric("Cooling", "Yes" if features.get("cooling") else "No")
                                st.metric("Cooling Type", features.get("coolingType", "N/A"))
                            
                            with col3:
                                st.metric("Garage", "Yes" if features.get("garage") else "No")
                                st.metric("Garage Spaces", features.get("garageSpaces", "N/A"))
                            
                            st.markdown("---")
                    
                    # Additional Info
                    with st.container():
                        st.markdown("**📋 Additional Information**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Legal Description", prop.get("legalDescription", "N/A"))
                        
                        with col2:
                            st.metric("Subdivision", prop.get("subdivision", "N/A"))
                
                with tab3:
                    st.markdown("### 💰 Financial Information")
                    
                    # Sale History Card
                    with st.container():
                        st.markdown("**💵 Sale Information**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Last Sale Date", format_date(prop.get("lastSaleDate")))
                        
                        with col2:
                            st.metric("Last Sale Price", format_currency(prop.get("lastSalePrice")))
                        
                        st.markdown("---")
                    
                    # Tax Assessments
                    if "taxAssessments" in prop and prop["taxAssessments"]:
                        st.markdown("**📊 Tax Assessments History**")
                        
                        assessments = prop["taxAssessments"]
                        assessment_data = []
                        
                        for year, data in assessments.items():
                            assessment_data.append({
                                "Year": year,
                                "Total Value": format_currency(data.get("value")),
                                "Land Value": format_currency(data.get("land")),
                                "Improvements": format_currency(data.get("improvements"))
                            })
                        
                        if assessment_data:
                            df = pd.DataFrame(assessment_data)
                            st.dataframe(df, use_container_width=True)
                        
                        st.markdown("---")
                    
                    # Property Taxes
                    if "propertyTaxes" in prop and prop["propertyTaxes"]:
                        st.markdown("**🏛️ Property Taxes History**")
                        
                        taxes = prop["propertyTaxes"]
                        tax_data = []
                        
                        for year, data in taxes.items():
                            tax_data.append({
                                "Year": year,
                                "Total Tax": format_currency(data.get("total"))
                            })
                        
                        if tax_data:
                            df = pd.DataFrame(tax_data)
                            st.dataframe(df, use_container_width=True)
                
                with tab4:
                    st.markdown("### 👤 Owner Information")
                    
                    if "owner" in prop and prop["owner"]:
                        owner = prop["owner"]
                        
                        with st.container():
                            st.markdown("**👤 Owner Details**")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                names = owner.get("names", [])
                                st.metric("Owner Name(s)", ", ".join(names) if names else "N/A")
                                st.metric("Owner Type", owner.get("type", "N/A"))
                            
                            with col2:
                                st.metric("Owner Occupied", "Yes" if prop.get("ownerOccupied") else "No")
                            
                            st.markdown("---")
                        
                        # Mailing Address
                        if "mailingAddress" in owner and owner["mailingAddress"]:
                            mailing = owner["mailingAddress"]
                            
                            with st.container():
                                st.markdown("**📮 Mailing Address**")
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Address", mailing.get("formattedAddress", "N/A"))
                                
                                with col2:
                                    st.metric("City", mailing.get("city", "N/A"))
                                
                                with col3:
                                    st.metric("State & ZIP", f"{mailing.get('state', 'N/A')} {mailing.get('zipCode', '')}")
                
                with tab5:
                    st.markdown("### 📋 Raw JSON Data")
                    
                    # Display complete JSON in expandable card
                    with st.expander("View Complete Property JSON", expanded=False):
                        json_str = json.dumps(property_data, indent=2)
                        st.code(json_str, language='json')
                    
                    # Property coordinates for mapping (if needed later)
                    if prop.get("latitude") and prop.get("longitude"):
                        st.markdown("**📍 Geographic Coordinates**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Latitude", prop.get("latitude"))
                        
                        with col2:
                            st.metric("Longitude", prop.get("longitude"))
            
            else:
                st.error("❌ No property data found. Please check the address and try again.")

# Tips section
st.markdown("---")
st.subheader("💡 Tips for Better Results")
st.markdown("""
- Include the full address with city, state, and ZIP code
- Use standard address formatting (e.g., "123 Main St, New York, NY 10001")
- Check spelling of street names and city names
- For apartments, include unit numbers when possible
""")

# Usage info
st.info("ℹ️ This search provides comprehensive property data including ownership, tax history, and detailed property features.")
