import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
from utils.auth import initialize_auth_state
from utils.search_database import get_user_searches, get_search_by_id
from utils.export_utils import (
    export_to_json, 
    export_to_csv, 
    export_to_excel, 
    export_to_pdf_report,
    get_export_summary
)

st.set_page_config(page_title="Downloads", page_icon="📥", layout="wide")

# Initialize auth state
initialize_auth_state()

# Check if user is authenticated
if st.session_state.user is None:
    st.warning("Please log in from the main page to access this feature.")
    st.stop()

st.title("📥 Downloads & Exports")
st.markdown("Export your property search data in various formats for analysis and reporting.")

# User info sidebar
with st.sidebar:
    st.subheader("Account Info")
    user_email = st.session_state.user.email
    user_id = st.session_state.user.id
    
    st.metric("Email", user_email)
    
    # Quick stats
    try:
        recent_searches = get_user_searches(user_id, limit=10)
        st.metric("Recent Searches", len(recent_searches))
    except Exception as e:
        st.warning("⚠️ Unable to load search count")

# Helper functions
def format_date(date_str):
    """Format date string for display"""
    if not date_str:
        return "N/A"
    try:
        if isinstance(date_str, str):
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

def get_property_results(search_data):
    """Extract property results from search data"""
    try:
        if isinstance(search_data, dict):
            if "results" in search_data:
                return search_data["results"]
            elif "property_data" in search_data and "results" in search_data["property_data"]:
                return search_data["property_data"]["results"]
        return []
    except:
        return []

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📋 Individual Downloads", "📦 Bulk Downloads", "📊 Export Analytics"])

with tab1:
    st.subheader("📋 Individual Search Downloads")
    st.markdown("Download specific searches in your preferred format.")
    
    # Search selection
    try:
        searches = get_user_searches(user_id, limit=50)
        
        if searches:
            # Search filter
            col1, col2 = st.columns([3, 1])
            with col1:
                search_filter = st.text_input("🔍 Filter searches", placeholder="Enter address to filter...")
            with col2:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            
            # Filter searches
            if search_filter:
                filtered_searches = []
                for search in searches:
                    address = get_search_address(search.get("property_data", {}))
                    if search_filter.lower() in address.lower():
                        filtered_searches.append(search)
                searches = filtered_searches
            
            if searches:
                # Search selection dropdown
                search_options = []
                for search in searches:
                    address = get_search_address(search.get("property_data", {}))
                    search_date = format_date(search.get("search_date", ""))
                    search_options.append(f"{address} - {search_date}")
                
                selected_index = st.selectbox(
                    "Select a search to download:",
                    range(len(search_options)),
                    format_func=lambda x: search_options[x]
                )
                
                selected_search = searches[selected_index]
                search_id = selected_search.get("id")
                property_data = selected_search.get("property_data", {})
                
                # Display search preview
                st.markdown("### 🔍 Search Preview")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Address", get_search_address(property_data))
                with col2:
                    results = get_property_results(property_data)
                    st.metric("Properties Found", len(results))
                with col3:
                    st.metric("Search Date", format_date(selected_search.get("search_date", "")))
                
                if results:
                    # Show first property as preview
                    with st.expander("📋 Property Preview", expanded=False):
                        prop = results[0]
                        
                        preview_col1, preview_col2, preview_col3 = st.columns(3)
                        with preview_col1:
                            st.write(f"**Type:** {prop.get('propertyType', 'N/A')}")
                            st.write(f"**Bedrooms:** {prop.get('bedrooms', 'N/A')}")
                        with preview_col2:
                            st.write(f"**Bathrooms:** {prop.get('bathrooms', 'N/A')}")
                            st.write(f"**Sq Ft:** {prop.get('squareFootage', 'N/A'):,}" if prop.get('squareFootage') else "**Sq Ft:** N/A")
                        with preview_col3:
                            st.write(f"**Year Built:** {prop.get('yearBuilt', 'N/A')}")
                            last_sale = prop.get('lastSalePrice')
                            st.write(f"**Last Sale:** ${last_sale:,}" if last_sale else "**Last Sale:** N/A")
                    
                    # Download options
                    st.markdown("### 📥 Download Options")
                    
                    download_col1, download_col2, download_col3, download_col4 = st.columns(4)
                    
                    with download_col1:
                        # JSON download
                        try:
                            json_data, json_filename = export_to_json(property_data, search_id)
                            st.download_button(
                                label="📄 JSON",
                                data=json_data,
                                file_name=json_filename,
                                mime="application/json",
                                use_container_width=True,
                                help="Raw data in JSON format"
                            )
                        except Exception as e:
                            st.error(f"JSON export error: {str(e)}")
                    
                    with download_col2:
                        # CSV download
                        try:
                            csv_data, csv_filename = export_to_csv(results, search_id)
                            st.download_button(
                                label="📊 CSV",
                                data=csv_data,
                                file_name=csv_filename,
                                mime="text/csv",
                                use_container_width=True,
                                help="Spreadsheet format for analysis"
                            )
                        except Exception as e:
                            st.error(f"CSV export error: {str(e)}")
                    
                    with download_col3:
                        # Excel download
                        try:
                            search_summary = get_export_summary(selected_search)
                            excel_bytes, excel_filename = export_to_excel(results, search_summary, search_id)
                            st.download_button(
                                label="📈 Excel",
                                data=excel_bytes,
                                file_name=excel_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                                help="Multi-sheet Excel workbook"
                            )
                        except Exception as e:
                            st.error(f"Excel export error: {str(e)}")
                    
                    with download_col4:
                        # PDF download
                        try:
                            search_summary = get_export_summary(selected_search)
                            pdf_bytes, pdf_filename = export_to_pdf_report(results, search_summary, search_id)
                            st.download_button(
                                label="📑 PDF Report",
                                data=pdf_bytes,
                                file_name=pdf_filename,
                                mime="application/pdf",
                                use_container_width=True,
                                help="Formatted PDF report"
                            )
                        except Exception as e:
                            st.error(f"PDF export error: {str(e)}")
                
                else:
                    st.warning("No property results found in this search.")
            
            else:
                st.info("No searches match your filter.")
        
        else:
            st.info("No searches found. Start by searching for properties on the Property Search page!")
    
    except Exception as e:
        st.error(f"Error loading searches: {str(e)}")

with tab2:
    st.subheader("📦 Bulk Downloads")
    st.markdown("Download multiple searches at once or create combined reports.")
    
    try:
        searches = get_user_searches(user_id, limit=100)
        
        if searches:
            # Date range filter
            st.markdown("### 📅 Filter by Date Range")
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                start_date = st.date_input(
                    "From Date",
                    value=datetime.now() - timedelta(days=30),
                    max_value=datetime.now().date()
                )
            
            with col2:
                end_date = st.date_input(
                    "To Date",
                    value=datetime.now().date(),
                    max_value=datetime.now().date()
                )
            
            with col3:
                st.write("")  # Spacer
                st.write("")  # Spacer
                apply_filter = st.button("Apply Filter", use_container_width=True)
            
            # Filter searches by date
            filtered_searches = []
            for search in searches:
                search_date_str = search.get("search_date", "")
                if search_date_str:
                    try:
                        if 'T' in search_date_str:
                            search_date = datetime.fromisoformat(search_date_str.replace('Z', '+00:00')).date()
                        else:
                            search_date = datetime.strptime(search_date_str, "%Y-%m-%d %H:%M:%S").date()
                        
                        if start_date <= search_date <= end_date:
                            filtered_searches.append(search)
                    except:
                        continue
            
            if filtered_searches:
                st.success(f"Found {len(filtered_searches)} searches in the selected date range")
                
                # Bulk download options
                st.markdown("### 📥 Bulk Export Options")
                
                bulk_col1, bulk_col2 = st.columns(2)
                
                with bulk_col1:
                    st.markdown("**📊 Combined Data Export**")
                    
                    # Combine all results
                    all_results = []
                    search_metadata = {
                        "export_type": "bulk_download",
                        "date_range": f"{start_date} to {end_date}",
                        "total_searches": len(filtered_searches),
                        "export_date": datetime.now().isoformat()
                    }
                    
                    for search in filtered_searches:
                        results = get_property_results(search.get("property_data", {}))
                        for result in results:
                            # Add search metadata to each result
                            result["search_id"] = search.get("id")
                            result["search_date"] = search.get("search_date")
                            result["search_address"] = get_search_address(search.get("property_data", {}))
                        all_results.extend(results)
                    
                    if all_results:
                        st.metric("Total Properties", len(all_results))
                        
                        # Combined CSV
                        try:
                            csv_data, csv_filename = export_to_csv(all_results, "bulk")
                            st.download_button(
                                label="📊 Download Combined CSV",
                                data=csv_data,
                                file_name=csv_filename,
                                mime="text/csv",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"CSV export error: {str(e)}")
                        
                        # Combined Excel
                        try:
                            excel_bytes, excel_filename = export_to_excel(all_results, search_metadata, "bulk")
                            st.download_button(
                                label="📈 Download Combined Excel",
                                data=excel_bytes,
                                file_name=excel_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Excel export error: {str(e)}")
                
                with bulk_col2:
                    st.markdown("**📑 Individual Search Archive**")
                    
                    # Create ZIP archive of individual searches
                    st.info("📦 ZIP Archive Feature")
                    st.markdown("""
                    Create a ZIP file containing individual exports for each search:
                    - Each search as separate CSV file
                    - Organized by date and address
                    - Includes search metadata
                    """)
                    
                    if st.button("🔄 Generate ZIP Archive", use_container_width=True):
                        st.info("ZIP archive generation coming soon!")
                
                # Search summary table
                st.markdown("### 📋 Searches in Date Range")
                
                summary_data = []
                for search in filtered_searches:
                    property_data = search.get("property_data", {})
                    results = get_property_results(property_data)
                    
                    summary_data.append({
                        "Date": format_date(search.get("search_date", "")),
                        "Address": get_search_address(property_data),
                        "Properties": len(results),
                        "Search ID": search.get("id")
                    })
                
                if summary_data:
                    df_summary = pd.DataFrame(summary_data)
                    st.dataframe(df_summary, use_container_width=True)
            
            else:
                st.info("No searches found in the selected date range.")
        
        else:
            st.info("No searches available for bulk download.")
    
    except Exception as e:
        st.error(f"Error loading bulk download data: {str(e)}")

with tab3:
    st.subheader("📊 Export Analytics")
    st.markdown("Track your download activity and export patterns.")
    
    try:
        searches = get_user_searches(user_id, limit=200)
        
        if searches:
            # Export statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Searches", len(searches))
            
            with col2:
                # Count searches with results
                searches_with_results = 0
                total_properties = 0
                for search in searches:
                    results = get_property_results(search.get("property_data", {}))
                    if results:
                        searches_with_results += 1
                        total_properties += len(results)
                
                st.metric("Searches with Results", searches_with_results)
            
            with col3:
                st.metric("Total Properties Found", total_properties)
            
            with col4:
                avg_properties = total_properties / searches_with_results if searches_with_results > 0 else 0
                st.metric("Avg Properties/Search", f"{avg_properties:.1f}")
            
            # Search activity chart
            st.markdown("### 📈 Search Activity Over Time")
            
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
                df_chart = pd.DataFrame(list(search_dates.items()), columns=["Date", "Searches"])
                df_chart["Date"] = pd.to_datetime(df_chart["Date"])
                df_chart = df_chart.sort_values("Date")
                
                st.line_chart(df_chart.set_index("Date"))
            
            # Most productive searches
            st.markdown("### 🏆 Most Productive Searches")
            
            productive_searches = []
            for search in searches:
                results = get_property_results(search.get("property_data", {}))
                if results:
                    productive_searches.append({
                        "Address": get_search_address(search.get("property_data", {})),
                        "Properties Found": len(results),
                        "Date": format_date(search.get("search_date", "")),
                        "Search ID": search.get("id")
                    })
            
            if productive_searches:
                # Sort by properties found
                productive_searches.sort(key=lambda x: x["Properties Found"], reverse=True)
                
                # Show top 10
                df_productive = pd.DataFrame(productive_searches[:10])
                st.dataframe(df_productive, use_container_width=True)
            
            # Export format recommendations
            st.markdown("### 💡 Export Format Recommendations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **📊 CSV Format**
                - Best for: Data analysis, spreadsheet work
                - Use when: Working with Excel, Google Sheets
                - Contains: Basic property information
                """)
                
                st.markdown("""
                **📈 Excel Format**
                - Best for: Complex analysis, multiple data views
                - Use when: Need tax assessments, property taxes
                - Contains: Multiple sheets with detailed data
                """)
            
            with col2:
                st.markdown("""
                **📄 JSON Format**
                - Best for: Developers, API integration
                - Use when: Building applications, data processing
                - Contains: Complete raw data structure
                """)
                
                st.markdown("""
                **📑 PDF Report**
                - Best for: Presentations, client reports
                - Use when: Sharing with non-technical users
                - Contains: Formatted, readable property reports
                """)
        
        else:
            st.info("No search data available for analytics.")
    
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

# Tips section
st.markdown("---")
st.subheader("💡 Download Tips")
st.markdown("""
- **Individual Downloads**: Perfect for specific property analysis
- **Bulk Downloads**: Combine multiple searches for comprehensive analysis
- **Format Selection**: Choose the right format for your intended use
- **Date Filtering**: Use date ranges to focus on recent or specific time periods
- **File Organization**: Downloaded files include timestamps for easy organization
""")

st.info("ℹ️ All downloads are generated in real-time and include the most current data from your searches.")

