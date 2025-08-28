import streamlit as st
import json
import pandas as pd
from datetime import datetime
from utils.auth import initialize_auth_state
from utils.search_database import (
    get_user_searches, 
    get_search_by_id, 
    delete_search, 
    get_search_statistics,
    save_named_search,
    get_saved_searches
)

st.set_page_config(page_title="Saved Searches", page_icon="📋")

# Initialize auth state
initialize_auth_state()

# Check if user is authenticated
if st.session_state.user is None:
    st.warning("Please log in from the main page to access this feature.")
    st.stop()

st.title("📋 Saved Searches")
st.markdown("View, manage, and download your property search history.")

# User info sidebar
with st.sidebar:
    st.subheader("Account Info")
    user_email = st.session_state.user.email
    user_id = st.session_state.user.id
    
    st.metric("Email", user_email)
    
    # Get search statistics
    try:
        stats = get_search_statistics(user_id)
        st.metric("Total Searches", stats.get("total_searches", 0))
        st.metric("Named Searches", stats.get("saved_searches", 0))
    except Exception as e:
        st.warning("⚠️ Unable to load search statistics")

# Helper functions
def format_date(date_str):
    """Format date string for display"""
    if not date_str:
        return "N/A"
    try:
        if isinstance(date_str, str):
            # Handle different date formats
            if 'T' in date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        else:
            date_obj = date_str
        return date_obj.strftime("%B %d, %Y at %I:%M %p")
    except:
        return str(date_str)

def get_search_address(search_data):
    """Extract address from search data"""
    try:
        if isinstance(search_data, dict):
            if "address" in search_data:
                return search_data["address"]
            elif "property_data" in search_data and "address" in search_data["property_data"]:
                return search_data["property_data"]["address"]
            elif "results" in search_data and len(search_data["results"]) > 0:
                return search_data["results"][0].get("formattedAddress", "Unknown Address")
        return "Unknown Address"
    except:
        return "Unknown Address"

def get_property_count(search_data):
    """Get number of properties found in search"""
    try:
        if isinstance(search_data, dict):
            if "results" in search_data:
                return len(search_data["results"])
            elif "property_data" in search_data and "results" in search_data["property_data"]:
                return len(search_data["property_data"]["results"])
        return 0
    except:
        return 0

def display_property_card(prop, index=0):
    """Display detailed property card with all available information"""
    with st.container():
        # Property header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### 🏠 {prop.get('formattedAddress', 'Unknown Address')}")
            st.markdown(f"**Property Type:** {prop.get('propertyType', 'N/A')}")
        
        with col2:
            if prop.get('lastSalePrice'):
                st.metric("Last Sale Price", f"${int(prop.get('lastSalePrice')):,}")
            else:
                st.metric("Last Sale Price", "N/A")
        
        # Basic property information
        st.markdown("#### 📊 Property Details")
        detail_cols = st.columns(4)
        
        with detail_cols[0]:
            st.metric("Bedrooms", prop.get('bedrooms', 'N/A'))
            st.metric("Bathrooms", prop.get('bathrooms', 'N/A'))
        
        with detail_cols[1]:
            sq_ft = prop.get('squareFootage')
            if sq_ft:
                st.metric("Square Footage", f"{int(sq_ft):,}")
            else:
                st.metric("Square Footage", "N/A")
            st.metric("Year Built", prop.get('yearBuilt', 'N/A'))
        
        with detail_cols[2]:
            lot_size = prop.get('lotSize')
            if lot_size:
                st.metric("Lot Size", f"{int(lot_size):,} sq ft")
            else:
                st.metric("Lot Size", "N/A")
            st.metric("Zoning", prop.get('zoning', 'N/A'))
        
        with detail_cols[3]:
            st.metric("County", prop.get('county', 'N/A'))
            st.metric("Subdivision", prop.get('subdivision', 'N/A'))
        
        # Property features
        features = prop.get('features', {})
        if features:
            st.markdown("#### 🏗️ Property Features")
            feature_cols = st.columns(3)
            
            with feature_cols[0]:
                st.markdown("**Structure:**")
                st.write(f"• Floors: {features.get('floorCount', 'N/A')}")
                st.write(f"• Rooms: {features.get('roomCount', 'N/A')}")
                st.write(f"• Units: {features.get('unitCount', 'N/A')}")
                st.write(f"• Architecture: {features.get('architectureType', 'N/A')}")
                st.write(f"• Exterior: {features.get('exteriorType', 'N/A')}")
                st.write(f"• Foundation: {features.get('foundationType', 'N/A')}")
            
            with feature_cols[1]:
                st.markdown("**Systems:**")
                st.write(f"• Heating: {features.get('heatingType', 'N/A') if features.get('heating') else 'None'}")
                st.write(f"• Cooling: {features.get('coolingType', 'N/A') if features.get('cooling') else 'None'}")
                st.write(f"• Roof: {features.get('roofType', 'N/A')}")
                if features.get('fireplace'):
                    st.write(f"• Fireplace: {features.get('fireplaceType', 'Yes')}")
                else:
                    st.write("• Fireplace: No")
            
            with feature_cols[2]:
                st.markdown("**Parking:**")
                if features.get('garage'):
                    st.write(f"• Garage Type: {features.get('garageType', 'N/A')}")
                    st.write(f"• Garage Spaces: {features.get('garageSpaces', 'N/A')}")
                else:
                    st.write("• Garage: No")
        
        # Owner information
        owner = prop.get('owner', {})
        if owner:
            st.markdown("#### 👤 Owner Information")
            owner_cols = st.columns(2)
            
            with owner_cols[0]:
                st.write(f"**Owner Type:** {owner.get('type', 'N/A')}")
                names = owner.get('names', [])
                if names:
                    st.write(f"**Owner Name(s):** {', '.join(names)}")
                st.write(f"**Owner Occupied:** {'Yes' if prop.get('ownerOccupied') else 'No'}")
            
            with owner_cols[1]:
                mailing_addr = owner.get('mailingAddress', {})
                if mailing_addr:
                    st.write(f"**Mailing Address:** {mailing_addr.get('formattedAddress', 'N/A')}")
        
        # Tax information
        tax_assessments = prop.get('taxAssessments', {})
        property_taxes = prop.get('propertyTaxes', {})
        
        if tax_assessments or property_taxes:
            st.markdown("#### 💰 Tax Information")
            
            # Create tax history dataframe
            tax_data = []
            years = set()
            if tax_assessments:
                years.update(tax_assessments.keys())
            if property_taxes:
                years.update(property_taxes.keys())
            
            for year in sorted(years, reverse=True):
                year_data = {"Year": year}
                
                if year in tax_assessments:
                    assessment = tax_assessments[year]
                    year_data["Assessed Value"] = f"${int(assessment.get('value', 0)):,}"
                    year_data["Land Value"] = f"${int(assessment.get('land', 0)):,}"
                    year_data["Improvement Value"] = f"${int(assessment.get('improvements', 0)):,}"
                
                if year in property_taxes:
                    year_data["Property Tax"] = f"${int(property_taxes[year].get('total', 0)):,}"
                
                tax_data.append(year_data)
            
            if tax_data:
                tax_df = pd.DataFrame(tax_data)
                st.dataframe(tax_df, use_container_width=True)
        
        # Sale history
        history = prop.get('history', {})
        if history:
            st.markdown("#### 📈 Sale History")
            history_data = []
            for date_str, sale_info in history.items():
                history_data.append({
                    "Date": format_date(sale_info.get('date')),
                    "Event": sale_info.get('event', 'N/A'),
                    "Price": f"${int(sale_info.get('price', 0)):,}" if sale_info.get('price') else 'N/A'
                })
            
            if history_data:
                history_df = pd.DataFrame(history_data)
                st.dataframe(history_df, use_container_width=True)
        
        # Location information
        if prop.get('latitude') and prop.get('longitude'):
            st.markdown("#### 📍 Location")
            location_cols = st.columns(2)
            
            with location_cols[0]:
                st.write(f"**Latitude:** {prop.get('latitude')}")
                st.write(f"**Longitude:** {prop.get('longitude')}")
            
            with location_cols[1]:
                st.write(f"**State FIPS:** {prop.get('stateFips', 'N/A')}")
                st.write(f"**County FIPS:** {prop.get('countyFips', 'N/A')}")
                st.write(f"**Assessor ID:** {prop.get('assessorID', 'N/A')}")
        
        # Legal description
        if prop.get('legalDescription'):
            st.markdown("#### ⚖️ Legal Description")
            st.write(prop.get('legalDescription'))

# Main content tabs
tab1, tab2, tab3 = st.tabs(["🔍 Search History", "⭐ Named Searches", "📊 Search Analytics"])

with tab1:
    st.subheader("🔍 Property Search History")
    st.markdown("All your property searches are automatically saved here with comprehensive details.")
    
    # Search filters
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_filter = st.text_input("🔍 Filter by address", placeholder="Enter address to filter...")
    with col2:
        limit = st.selectbox("Results per page", [10, 25, 50, 100], index=1)
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Get user searches
    try:
        searches = get_user_searches(user_id, limit=limit)
        
        if searches:
            # Filter searches if search term provided
            if search_filter:
                filtered_searches = []
                for search in searches:
                    address = get_search_address(search.get("property_data", {}))
                    if search_filter.lower() in address.lower():
                        filtered_searches.append(search)
                searches = filtered_searches
            
            if searches:
                st.success(f"Found {len(searches)} search(es)")
                
                # Display searches in enhanced cards
                for i, search in enumerate(searches):
                    search_id = search.get("id")
                    search_date = search.get("search_date")
                    property_data = search.get("property_data", {})
                    
                    address = get_search_address(property_data)
                    property_count = get_property_count(property_data)
                    
                    with st.container():
                        st.markdown("---")
                        
                        # Search card header
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"**📍 {address}**")
                            st.caption(f"🕒 {format_date(search_date)}")
                        
                        with col2:
                            st.metric("Properties", property_count)
                        
                        with col3:
                            if st.button("👁️ View Details", key=f"view_{search_id}", use_container_width=True):
                                st.session_state[f"show_details_{search_id}"] = not st.session_state.get(f"show_details_{search_id}", False)
                        
                        with col4:
                            if st.button("🗑️ Delete", key=f"delete_{search_id}", use_container_width=True, type="secondary"):
                                if st.session_state.get(f"confirm_delete_{search_id}", False):
                                    # Perform deletion
                                    delete_result = delete_search(search_id, user_id)
                                    if delete_result.get("success"):
                                        st.success("Search deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete: {delete_result.get('message')}")
                                else:
                                    st.session_state[f"confirm_delete_{search_id}"] = True
                                    st.warning("Click delete again to confirm")
                        
                        # Show detailed property information if requested
                        if st.session_state.get(f"show_details_{search_id}", False):
                            with st.expander("🔍 Comprehensive Property Details", expanded=True):
                                
                                # Display property results with full details
                                if property_data and "results" in property_data:
                                    results = property_data["results"]
                                    if results and len(results) > 0:
                                        for idx, prop in enumerate(results):
                                            if len(results) > 1:
                                                st.markdown(f"### Property {idx + 1} of {len(results)}")
                                            
                                            display_property_card(prop, idx)
                                            
                                            if idx < len(results) - 1:
                                                st.markdown("---")
                                        
                                        # Download options
                                        st.markdown("---")
                                        st.markdown("### 📥 Download Options")
                                        download_col1, download_col2, download_col3 = st.columns(3)
                                        
                                        with download_col1:
                                            # JSON download
                                            json_data = json.dumps(property_data, indent=2)
                                            st.download_button(
                                                label="📄 Download as JSON",
                                                data=json_data,
                                                file_name=f"property_search_{search_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                                mime="application/json",
                                                use_container_width=True
                                            )
                                        
                                        with download_col2:
                                            # CSV download (comprehensive data)
                                            try:
                                                df_data = []
                                                for prop in results:
                                                    # Basic property info
                                                    row_data = {
                                                        "Address": prop.get("formattedAddress", "N/A"),
                                                        "Property Type": prop.get("propertyType", "N/A"),
                                                        "Bedrooms": prop.get("bedrooms", "N/A"),
                                                        "Bathrooms": prop.get("bathrooms", "N/A"),
                                                        "Square Footage": prop.get("squareFootage", "N/A"),
                                                        "Lot Size": prop.get("lotSize", "N/A"),
                                                        "Year Built": prop.get("yearBuilt", "N/A"),
                                                        "Last Sale Price": prop.get("lastSalePrice", "N/A"),
                                                        "Last Sale Date": prop.get("lastSaleDate", "N/A"),
                                                        "County": prop.get("county", "N/A"),
                                                        "Zoning": prop.get("zoning", "N/A"),
                                                        "Owner Occupied": prop.get("ownerOccupied", "N/A"),
                                                        "Subdivision": prop.get("subdivision", "N/A")
                                                    }
                                                    
                                                    # Add latest tax assessment
                                                    tax_assessments = prop.get("taxAssessments", {})
                                                    if tax_assessments:
                                                        latest_year = max(tax_assessments.keys())
                                                        latest_assessment = tax_assessments[latest_year]
                                                        row_data["Latest Assessed Value"] = latest_assessment.get("value", "N/A")
                                                        row_data["Latest Land Value"] = latest_assessment.get("land", "N/A")
                                                        row_data["Latest Improvement Value"] = latest_assessment.get("improvements", "N/A")
                                                    
                                                    # Add latest property tax
                                                    property_taxes = prop.get("propertyTaxes", {})
                                                    if property_taxes:
                                                        latest_tax_year = max(property_taxes.keys())
                                                        row_data["Latest Property Tax"] = property_taxes[latest_tax_year].get("total", "N/A")
                                                    
                                                    # Add features
                                                    features = prop.get("features", {})
                                                    if features:
                                                        row_data["Garage"] = "Yes" if features.get("garage") else "No"
                                                        row_data["Garage Spaces"] = features.get("garageSpaces", "N/A")
                                                        row_data["Heating"] = features.get("heatingType", "N/A")
                                                        row_data["Cooling"] = features.get("coolingType", "N/A")
                                                        row_data["Fireplace"] = "Yes" if features.get("fireplace") else "No"
                                                        row_data["Floor Count"] = features.get("floorCount", "N/A")
                                                        row_data["Room Count"] = features.get("roomCount", "N/A")
                                                    
                                                    df_data.append(row_data)
                                                
                                                df = pd.DataFrame(df_data)
                                                csv_data = df.to_csv(index=False)
                                                
                                                st.download_button(
                                                    label="📊 Download as CSV",
                                                    data=csv_data,
                                                    file_name=f"property_search_{search_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                                    mime="text/csv",
                                                    use_container_width=True
                                                )
                                            except Exception as e:
                                                st.error(f"CSV generation failed: {str(e)}")
                                        
                                        with download_col3:
                                            # Excel download with multiple sheets
                                            try:
                                                import io
                                                from openpyxl import Workbook
                                                
                                                # Create Excel file in memory
                                                output = io.BytesIO()
                                                
                                                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                                    # Basic property info sheet
                                                    basic_df = pd.DataFrame(df_data)
                                                    basic_df.to_excel(writer, sheet_name='Property Details', index=False)
                                                    
                                                    # Tax history sheet
                                                    tax_history_data = []
                                                    for prop in results:
                                                        address = prop.get("formattedAddress", "N/A")
                                                        tax_assessments = prop.get("taxAssessments", {})
                                                        property_taxes = prop.get("propertyTaxes", {})
                                                        
                                                        years = set()
                                                        if tax_assessments:
                                                            years.update(tax_assessments.keys())
                                                        if property_taxes:
                                                            years.update(property_taxes.keys())
                                                        
                                                        for year in years:
                                                            row = {"Address": address, "Year": year}
                                                            if year in tax_assessments:
                                                                assessment = tax_assessments[year]
                                                                row["Assessed Value"] = assessment.get("value", "")
                                                                row["Land Value"] = assessment.get("land", "")
                                                                row["Improvement Value"] = assessment.get("improvements", "")
                                                            if year in property_taxes:
                                                                row["Property Tax"] = property_taxes[year].get("total", "")
                                                            tax_history_data.append(row)
                                                    
                                                    if tax_history_data:
                                                        tax_df = pd.DataFrame(tax_history_data)
                                                        tax_df.to_excel(writer, sheet_name='Tax History', index=False)
                                                
                                                excel_data = output.getvalue()
                                                
                                                st.download_button(
                                                    label="📈 Download as Excel",
                                                    data=excel_data,
                                                    file_name=f"property_search_{search_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                                    use_container_width=True
                                                )
                                            except Exception as e:
                                                st.error(f"Excel generation failed: {str(e)}")
                                
                                else:
                                    st.info("No detailed property data available for this search.")
            else:
                st.info("No searches found matching your filter.")
        else:
            st.info("No searches found. Start by searching for properties on the Property Search page!")
            
    except Exception as e:
        st.error(f"Error loading searches: {str(e)}")

with tab2:
    st.subheader("⭐ Named Searches")
    st.markdown("Save search criteria with custom names for easy reuse.")
    
    # Add new named search
    with st.expander("➕ Create New Named Search", expanded=False):
        with st.form("new_named_search"):
            search_name = st.text_input("Search Name", placeholder="e.g., Downtown Condos Under 500K")
            search_address = st.text_input("Address/Location", placeholder="e.g., Downtown Seattle, WA")
            
            col1, col2 = st.columns(2)
            with col1:
                min_bedrooms = st.number_input("Min Bedrooms", min_value=0, max_value=10, value=0)
                min_bathrooms = st.number_input("Min Bathrooms", min_value=0, max_value=10, value=0)
            
            with col2:
                max_price = st.number_input("Max Price", min_value=0, value=0, help="0 = no limit")
                property_type = st.selectbox("Property Type", ["Any", "Single Family", "Condo", "Townhouse", "Multi-Family"])
            
            auto_notify = st.checkbox("Auto-notify when new properties match", value=False)
            
            if st.form_submit_button("💾 Save Named Search", use_container_width=True):
                if search_name and search_address:
                    search_criteria = {
                        "address": search_address,
                        "min_bedrooms": min_bedrooms,
                        "min_bathrooms": min_bathrooms,
                        "max_price": max_price if max_price > 0 else None,
                        "property_type": property_type if property_type != "Any" else None
                    }
                    
                    result = save_named_search(user_id, search_name, search_criteria, auto_notify)
                    if result.get("success"):
                        st.success("Named search saved successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to save: {result.get('message')}")
                else:
                    st.error("Please provide both search name and address/location.")
    
    # Display existing named searches
    try:
        named_searches = get_saved_searches(user_id)
        
        if named_searches:
            st.success(f"You have {len(named_searches)} named search(es)")
            
            for search in named_searches:
                search_id = search.get("id")
                search_name = search.get("search_name")
                search_criteria = search.get("search_criteria", {})
                created_at = search.get("created_at")
                last_run = search.get("last_run")
                results_count = search.get("results_count", 0)
                auto_notify = search.get("auto_notify", False)
                
                with st.container():
                    st.markdown("---")
                    
                    # Named search card
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**⭐ {search_name}**")
                        st.caption(f"📍 {search_criteria.get('address', 'N/A')}")
                        st.caption(f"🕒 Created: {format_date(created_at)}")
                        if last_run:
                            st.caption(f"🔄 Last run: {format_date(last_run)}")
                    
                    with col2:
                        st.metric("Results", results_count)
                        if auto_notify:
                            st.caption("🔔 Auto-notify ON")
                    
                    with col3:
                        if st.button("🔍 Run Search", key=f"run_{search_id}", use_container_width=True):
                            st.info("Feature coming soon: Run saved search")
                        
                        if st.button("🗑️ Delete", key=f"delete_named_{search_id}", use_container_width=True, type="secondary"):
                            st.info("Feature coming soon: Delete named search")
                    
                    # Show criteria details
                    with st.expander("📋 Search Criteria", expanded=False):
                        criteria_cols = st.columns(2)
                        
                        with criteria_cols[0]:
                            st.write(f"**Address/Location:** {search_criteria.get('address', 'N/A')}")
                            st.write(f"**Min Bedrooms:** {search_criteria.get('min_bedrooms', 'Any')}")
                            st.write(f"**Min Bathrooms:** {search_criteria.get('min_bathrooms', 'Any')}")
                        
                        with criteria_cols[1]:
                            max_price = search_criteria.get('max_price')
                            if max_price:
                                st.write(f"**Max Price:** ${int(max_price):,}")
                            else:
                                st.write("**Max Price:** No limit")
                            st.write(f"**Property Type:** {search_criteria.get('property_type', 'Any')}")
                            st.write(f"**Auto-notify:** {'Yes' if auto_notify else 'No'}")
        else:
            st.info("No named searches found. Create your first named search above!")
            
    except Exception as e:
        st.error(f"Error loading named searches: {str(e)}")

with tab3:
    st.subheader("📊 Search Analytics")
    st.markdown("Analyze your search patterns and property market trends.")
    
    try:
        # Get all user searches for analytics
        all_searches = get_user_searches(user_id, limit=1000)
        
        if all_searches and len(all_searches) > 0:
            # Create analytics dataframe
            analytics_data = []
            for search in all_searches:
                property_data = search.get("property_data", {})
                results = property_data.get("results", [])
                
                for prop in results:
                    analytics_data.append({
                        "search_date": search.get("search_date"),
                        "address": prop.get("formattedAddress", ""),
                        "property_type": prop.get("propertyType", ""),
                        "bedrooms": prop.get("bedrooms"),
                        "bathrooms": prop.get("bathrooms"),
                        "square_footage": prop.get("squareFootage"),
                        "year_built": prop.get("yearBuilt"),
                        "last_sale_price": prop.get("lastSalePrice"),
                        "county": prop.get("county", ""),
                        "city": prop.get("city", ""),
                        "state": prop.get("state", "")
                    })
            
            if analytics_data:
                df = pd.DataFrame(analytics_data)
                
                # Search frequency over time
                st.markdown("#### 📈 Search Activity Over Time")
                df['search_date'] = pd.to_datetime(df['search_date'])
                search_counts = df.groupby(df['search_date'].dt.date).size().reset_index()
                search_counts.columns = ['Date', 'Searches']
                
                st.line_chart(search_counts.set_index('Date'))
                
                # Property type distribution
                st.markdown("#### 🏠 Property Types Searched")
                prop_type_counts = df['property_type'].value_counts()
                st.bar_chart(prop_type_counts)
                
                # Price range analysis
                st.markdown("#### 💰 Price Range Analysis")
                price_data = df[df['last_sale_price'].notna() & (df['last_sale_price'] > 0)]
                if not price_data.empty:
                    price_cols = st.columns(3)
                    
                    with price_cols[0]:
                        st.metric("Average Price", f"${int(price_data['last_sale_price'].mean()):,}")
                    
                    with price_cols[1]:
                        st.metric("Median Price", f"${int(price_data['last_sale_price'].median()):,}")
                    
                    with price_cols[2]:
                        st.metric("Price Range", f"${int(price_data['last_sale_price'].min()):,} - ${int(price_data['last_sale_price'].max()):,}")
                    
                    # Price distribution histogram
                    st.histogram(price_data['last_sale_price'], bins=20)
                
                # Geographic distribution
                st.markdown("#### 🗺️ Geographic Distribution")
                geo_cols = st.columns(2)
                
                with geo_cols[0]:
                    county_counts = df['county'].value_counts().head(10)
                    st.bar_chart(county_counts)
                    st.caption("Top Counties Searched")
                
                with geo_cols[1]:
                    state_counts = df['state'].value_counts().head(10)
                    st.bar_chart(state_counts)
                    st.caption("States Searched")
                
                # Property characteristics
                st.markdown("#### 🏗️ Property Characteristics")
                char_cols = st.columns(3)
                
                with char_cols[0]:
                    bedroom_counts = df['bedrooms'].value_counts().sort_index()
                    st.bar_chart(bedroom_counts)
                    st.caption("Bedrooms Distribution")
                
                with char_cols[1]:
                    bathroom_counts = df['bathrooms'].value_counts().sort_index()
                    st.bar_chart(bathroom_counts)
                    st.caption("Bathrooms Distribution")
                
                with char_cols[2]:
                    # Year built distribution
                    year_data = df[df['year_built'].notna()]
                    if not year_data.empty:
                        year_bins = pd.cut(year_data['year_built'], bins=10)
                        year_counts = year_bins.value_counts().sort_index()
                        st.bar_chart(year_counts)
                        st.caption("Year Built Distribution")
                
                # Summary statistics
                st.markdown("#### 📋 Summary Statistics")
                summary_cols = st.columns(4)
                
                with summary_cols[0]:
                    st.metric("Total Properties Viewed", len(df))
                
                with summary_cols[1]:
                    st.metric("Unique Searches", len(all_searches))
                
                with summary_cols[2]:
                    unique_locations = df['address'].nunique()
                    st.metric("Unique Properties", unique_locations)
                
                with summary_cols[3]:
                    avg_props_per_search = len(df) / len(all_searches) if all_searches else 0
                    st.metric("Avg Properties/Search", f"{avg_props_per_search:.1f}")
                
            else:
                st.info("No property data available for analytics.")
        else:
            st.info("No search data available for analytics. Start searching for properties to see analytics!")
            
    except Exception as e:
        st.error(f"Error generating analytics: {str(e)}")

