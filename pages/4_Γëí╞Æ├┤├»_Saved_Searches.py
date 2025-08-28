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

# Main content tabs
tab1, tab2, tab3 = st.tabs(["🔍 Search History", "⭐ Named Searches", "📊 Search Analytics"])

with tab1:
    st.subheader("🔍 Property Search History")
    st.markdown("All your property searches are automatically saved here.")
    
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
                
                # Display searches in cards
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
                            if st.button("👁️ View", key=f"view_{search_id}", use_container_width=True):
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
                        
                        # Show details if requested
                        if st.session_state.get(f"show_details_{search_id}", False):
                            with st.expander("🔍 Search Details", expanded=True):
                                
                                # Display property results
                                if property_data and "results" in property_data:
                                    results = property_data["results"]
                                    if results and len(results) > 0:
                                        prop = results[0]  # Show first property
                                        
                                        # Basic info
                                        detail_col1, detail_col2, detail_col3 = st.columns(3)
                                        
                                        with detail_col1:
                                            st.metric("Property Type", prop.get("propertyType", "N/A"))
                                            st.metric("Bedrooms", prop.get("bedrooms", "N/A"))
                                        
                                        with detail_col2:
                                            st.metric("Bathrooms", prop.get("bathrooms", "N/A"))
                                            st.metric("Square Footage", f"{prop.get('squareFootage', 'N/A'):,}" if prop.get('squareFootage') else "N/A")
                                        
                                        with detail_col3:
                                            st.metric("Year Built", prop.get("yearBuilt", "N/A"))
                                            last_sale = prop.get("lastSalePrice")
                                            if last_sale:
                                                st.metric("Last Sale Price", f"${int(last_sale):,}")
                                            else:
                                                st.metric("Last Sale Price", "N/A")
                                        
                                        # Download options
                                        st.markdown("**📥 Download Options**")
                                        download_col1, download_col2 = st.columns(2)
                                        
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
                                            # CSV download (basic info)
                                            try:
                                                df_data = []
                                                for prop in results:
                                                    df_data.append({
                                                        "Address": prop.get("formattedAddress", "N/A"),
                                                        "Property Type": prop.get("propertyType", "N/A"),
                                                        "Bedrooms": prop.get("bedrooms", "N/A"),
                                                        "Bathrooms": prop.get("bathrooms", "N/A"),
                                                        "Square Footage": prop.get("squareFootage", "N/A"),
                                                        "Year Built": prop.get("yearBuilt", "N/A"),
                                                        "Last Sale Price": prop.get("lastSalePrice", "N/A"),
                                                        "Last Sale Date": prop.get("lastSaleDate", "N/A")
                                                    })
                                                
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
                        criteria_col1, criteria_col2 = st.columns(2)
                        
                        with criteria_col1:
                            st.write(f"**Address:** {search_criteria.get('address', 'N/A')}")
                            st.write(f"**Min Bedrooms:** {search_criteria.get('min_bedrooms', 'Any')}")
                            st.write(f"**Min Bathrooms:** {search_criteria.get('min_bathrooms', 'Any')}")
                        
                        with criteria_col2:
                            max_price = search_criteria.get('max_price')
                            st.write(f"**Max Price:** ${max_price:,}" if max_price else "**Max Price:** No limit")
                            st.write(f"**Property Type:** {search_criteria.get('property_type', 'Any')}")
                            st.write(f"**Auto-notify:** {'Yes' if auto_notify else 'No'}")
        else:
            st.info("No named searches yet. Create one above to get started!")
            
    except Exception as e:
        st.error(f"Error loading named searches: {str(e)}")

with tab3:
    st.subheader("📊 Search Analytics")
    st.markdown("Overview of your search activity and patterns.")
    
    try:
        stats = get_search_statistics(user_id)
        searches = get_user_searches(user_id, limit=100)  # Get more for analytics
        
        # Basic stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Searches", stats.get("total_searches", 0))
        
        with col2:
            st.metric("Named Searches", stats.get("saved_searches", 0))
        
        with col3:
            # Calculate searches this month
            current_month = datetime.now().strftime("%Y-%m")
            monthly_searches = 0
            for search in searches:
                search_date = search.get("search_date", "")
                if search_date and search_date.startswith(current_month):
                    monthly_searches += 1
            st.metric("This Month", monthly_searches)
        
        with col4:
            # Most recent search
            if searches:
                last_search_date = searches[0].get("search_date", "")
                st.metric("Last Search", format_date(last_search_date).split(" at ")[0] if last_search_date else "N/A")
            else:
                st.metric("Last Search", "N/A")
        
        # Search frequency chart
        if searches and len(searches) > 1:
            st.markdown("### 📈 Search Activity")
            
            # Group searches by date
            search_dates = {}
            for search in searches:
                search_date = search.get("search_date", "")
                if search_date:
                    try:
                        date_key = search_date.split("T")[0]  # Get just the date part
                        search_dates[date_key] = search_dates.get(date_key, 0) + 1
                    except:
                        continue
            
            if search_dates:
                # Create DataFrame for chart
                df_chart = pd.DataFrame(list(search_dates.items()), columns=["Date", "Searches"])
                df_chart["Date"] = pd.to_datetime(df_chart["Date"])
                df_chart = df_chart.sort_values("Date")
                
                st.line_chart(df_chart.set_index("Date"))
        
        # Most searched locations
        if searches:
            st.markdown("### 📍 Most Searched Locations")
            
            location_counts = {}
            for search in searches:
                address = get_search_address(search.get("property_data", {}))
                if address != "Unknown Address":
                    # Extract city/area from address
                    try:
                        parts = address.split(",")
                        if len(parts) >= 2:
                            location = parts[-2].strip()  # Get city
                        else:
                            location = address
                        location_counts[location] = location_counts.get(location, 0) + 1
                    except:
                        continue
            
            if location_counts:
                # Sort by count and show top 10
                sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                
                for i, (location, count) in enumerate(sorted_locations, 1):
                    st.write(f"{i}. **{location}** - {count} search(es)")
        
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

# Tips section
st.markdown("---")
st.subheader("💡 Tips")
st.markdown("""
- **Search History**: All your property searches are automatically saved
- **Named Searches**: Create reusable search templates with custom criteria
- **Downloads**: Export search results as JSON or CSV files
- **Auto-notify**: Get notified when new properties match your saved searches (coming soon)
- **Analytics**: Track your search patterns and most searched locations
""")

st.info("ℹ️ Your search data is securely stored and only accessible to you.")

