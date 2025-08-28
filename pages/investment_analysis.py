import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List, Optional
from utils.auth import initialize_auth_state, get_current_user
from utils.search_database import get_user_searches, get_supabase_client
from utils.investment_calculator import (
    calculate_cash_flow,
    calculate_cap_rate,
    calculate_cash_on_cash_return,
    calculate_roi,
    calculate_break_even_analysis,
    calculate_appreciation_scenarios,
    calculate_tax_benefits,
    generate_investment_report
)

st.set_page_config(page_title="Investment Analysis", page_icon="📊", layout="wide")

# Initialize auth state
initialize_auth_state()

# Check if user is authenticated
if st.session_state.user is None:
    st.warning("Please log in from the main page to access this feature.")
    st.stop()

st.title("📊 Real Estate Investment Analysis")
st.markdown("Comprehensive financial analysis tools for property investment decisions.")

# User info sidebar
with st.sidebar:
    st.subheader("Investment Tools")
    user_email = st.session_state.user.email
    st.metric("User", user_email)
    
    analysis_type = st.selectbox(
        "Analysis Type",
        ["Property Analysis", "Portfolio Overview", "Market Comparison", "Scenario Planning"]
    )
    
    st.markdown("---")
    st.subheader("Quick Actions")
    if st.button("📥 Import Property Data", use_container_width=True):
        st.session_state.show_import = True
    
    if st.button("💾 Save Analysis", use_container_width=True):
        st.session_state.show_save = True
    
    if st.button("📈 Generate Report", use_container_width=True):
        st.session_state.show_report = True

def load_property_from_searches(user_id: str) -> List[Dict[str, Any]]:
    """Load properties from user's saved searches"""
    try:
        searches = get_user_searches(user_id, limit=100)
        properties = []
        
        for search in searches:
            property_data = search.get("property_data", {})
            results = property_data.get("results", [])
            
            for prop in results:
                # Extract key investment data
                investment_prop = {
                    "id": prop.get("id", ""),
                    "address": prop.get("formattedAddress", ""),
                    "property_type": prop.get("propertyType", ""),
                    "bedrooms": prop.get("bedrooms", 0),
                    "bathrooms": prop.get("bathrooms", 0),
                    "square_footage": prop.get("squareFootage", 0),
                    "lot_size": prop.get("lotSize", 0),
                    "year_built": prop.get("yearBuilt", 0),
                    "last_sale_price": prop.get("lastSalePrice", 0),
                    "last_sale_date": prop.get("lastSaleDate", ""),
                    "county": prop.get("county", ""),
                    "state": prop.get("state", ""),
                    "zoning": prop.get("zoning", ""),
                    "owner_occupied": prop.get("ownerOccupied", False),
                    "latitude": prop.get("latitude", 0),
                    "longitude": prop.get("longitude", 0)
                }
                
                # Add tax information
                tax_assessments = prop.get("taxAssessments", {})
                property_taxes = prop.get("propertyTaxes", {})
                
                if tax_assessments:
                    latest_year = max(tax_assessments.keys())
                    latest_assessment = tax_assessments[latest_year]
                    investment_prop.update({
                        "assessed_value": latest_assessment.get("value", 0),
                        "land_value": latest_assessment.get("land", 0),
                        "improvement_value": latest_assessment.get("improvements", 0)
                    })
                
                if property_taxes:
                    latest_tax_year = max(property_taxes.keys())
                    investment_prop["annual_property_tax"] = property_taxes[latest_tax_year].get("total", 0)
                
                properties.append(investment_prop)
        
        return properties
        
    except Exception as e:
        st.error(f"Error loading properties: {str(e)}")
        return []

def save_investment_analysis(user_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save investment analysis to Supabase"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return {"success": False, "message": "Database connection not available"}
        
        analysis_record = {
            "user_id": user_id,
            "analysis_data": analysis_data,
            "created_at": datetime.now().isoformat(),
            "analysis_type": analysis_data.get("type", "property_analysis")
        }
        
        response = supabase.table("investment_analyses").insert(analysis_record).execute()
        
        if response.data:
            return {"success": True, "analysis_id": response.data[0]["id"]}
        else:
            return {"success": False, "message": "Failed to save analysis"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_user_analyses(user_id: str) -> List[Dict[str, Any]]:
    """Get user's saved investment analyses"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        response = supabase.table("investment_analyses").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data if response.data else []
        
    except Exception as e:
        return []

# Main content based on analysis type
if analysis_type == "Property Analysis":
    st.subheader("🏠 Individual Property Investment Analysis")
    
    # Property selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Load properties from searches
        properties = load_property_from_searches(st.session_state.user.id)
        
        if properties:
            property_options = [f"{prop['address']} - ${prop['last_sale_price']:,}" if prop['last_sale_price'] else f"{prop['address']} - No sale price" for prop in properties]
            selected_property_idx = st.selectbox("Select Property from Your Searches", range(len(property_options)), format_func=lambda x: property_options[x])
            selected_property = properties[selected_property_idx] if selected_property_idx is not None else None
        else:
            st.info("No properties found in your searches. Search for properties first or enter manual data below.")
            selected_property = None
    
    with col2:
        st.markdown("**Or enter property manually:**")
        manual_entry = st.checkbox("Manual Property Entry")
    
    # Property input form
    if manual_entry or not selected_property:
        st.markdown("### 📝 Property Information")
        
        with st.form("property_input"):
            prop_col1, prop_col2, prop_col3 = st.columns(3)
            
            with prop_col1:
                address = st.text_input("Property Address", value=selected_property.get("address", "") if selected_property else "")
                purchase_price = st.number_input("Purchase Price ($)", min_value=0, value=int(selected_property.get("last_sale_price", 0)) if selected_property and selected_property.get("last_sale_price") else 200000)
                down_payment_pct = st.slider("Down Payment (%)", min_value=0, max_value=100, value=20)
                loan_term = st.selectbox("Loan Term (years)", [15, 20, 25, 30], index=3)
            
            with prop_col2:
                interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=20.0, value=6.5, step=0.1)
                monthly_rent = st.number_input("Monthly Rent ($)", min_value=0, value=1800)
                vacancy_rate = st.slider("Vacancy Rate (%)", min_value=0, max_value=50, value=5)
                annual_rent_increase = st.slider("Annual Rent Increase (%)", min_value=0, max_value=10, value=3)
            
            with prop_col3:
                property_tax = st.number_input("Annual Property Tax ($)", min_value=0, value=int(selected_property.get("annual_property_tax", 0)) if selected_property and selected_property.get("annual_property_tax") else 3000)
                insurance = st.number_input("Annual Insurance ($)", min_value=0, value=1200)
                maintenance_pct = st.slider("Maintenance (% of rent)", min_value=0, max_value=20, value=8)
                management_pct = st.slider("Property Management (% of rent)", min_value=0, max_value=15, value=10)
            
            calculate_button = st.form_submit_button("🧮 Calculate Investment Metrics", use_container_width=True)
    else:
        # Use selected property data
        address = selected_property.get("address", "")
        purchase_price = int(selected_property.get("last_sale_price", 0)) if selected_property.get("last_sale_price") else 200000
        property_tax = int(selected_property.get("annual_property_tax", 0)) if selected_property.get("annual_property_tax") else 3000
        
        # Show property details
        st.markdown("### 🏠 Selected Property Details")
        detail_cols = st.columns(4)
        
        with detail_cols[0]:
            st.metric("Address", address)
            st.metric("Property Type", selected_property.get("property_type", "N/A"))
        
        with detail_cols[1]:
            st.metric("Bedrooms", selected_property.get("bedrooms", "N/A"))
            st.metric("Bathrooms", selected_property.get("bathrooms", "N/A"))
        
        with detail_cols[2]:
            sq_ft = selected_property.get("square_footage", 0)
            if sq_ft:
                st.metric("Square Footage", f"{int(sq_ft):,}")
            else:
                st.metric("Square Footage", "N/A")
            st.metric("Year Built", selected_property.get("year_built", "N/A"))
        
        with detail_cols[3]:
            if purchase_price:
                st.metric("Last Sale Price", f"${purchase_price:,}")
            else:
                st.metric("Last Sale Price", "N/A")
            if property_tax:
                st.metric("Annual Property Tax", f"${property_tax:,}")
            else:
                st.metric("Annual Property Tax", "N/A")
        
        # Investment parameters
        st.markdown("### 💰 Investment Parameters")
        param_cols = st.columns(4)
        
        with param_cols[0]:
            down_payment_pct = st.slider("Down Payment (%)", min_value=0, max_value=100, value=20)
            loan_term = st.selectbox("Loan Term (years)", [15, 20, 25, 30], index=3)
        
        with param_cols[1]:
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=20.0, value=6.5, step=0.1)
            monthly_rent = st.number_input("Monthly Rent ($)", min_value=0, value=1800)
        
        with param_cols[2]:
            vacancy_rate = st.slider("Vacancy Rate (%)", min_value=0, max_value=50, value=5)
            annual_rent_increase = st.slider("Annual Rent Increase (%)", min_value=0, max_value=10, value=3)
        
        with param_cols[3]:
            insurance = st.number_input("Annual Insurance ($)", min_value=0, value=1200)
            maintenance_pct = st.slider("Maintenance (% of rent)", min_value=0, max_value=20, value=8)
            management_pct = st.slider("Property Management (% of rent)", min_value=0, max_value=15, value=10)
        
        calculate_button = st.button("🧮 Calculate Investment Metrics", use_container_width=True)
    
    # Perform calculations
    if calculate_button and purchase_price > 0:
        # Calculate investment metrics
        down_payment = purchase_price * (down_payment_pct / 100)
        loan_amount = purchase_price - down_payment
        
        # Monthly calculations
        monthly_interest_rate = (interest_rate / 100) / 12
        num_payments = loan_term * 12
        
        if monthly_interest_rate > 0:
            monthly_payment = loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate)**num_payments) / ((1 + monthly_interest_rate)**num_payments - 1)
        else:
            monthly_payment = loan_amount / num_payments
        
        annual_rent = monthly_rent * 12
        effective_annual_rent = annual_rent * (1 - vacancy_rate / 100)
        
        # Annual expenses
        annual_maintenance = effective_annual_rent * (maintenance_pct / 100)
        annual_management = effective_annual_rent * (management_pct / 100)
        annual_mortgage = monthly_payment * 12
        
        total_annual_expenses = annual_mortgage + property_tax + insurance + annual_maintenance + annual_management
        
        # Key metrics
        annual_cash_flow = effective_annual_rent - total_annual_expenses
        monthly_cash_flow = annual_cash_flow / 12
        
        cap_rate = (effective_annual_rent - (property_tax + insurance + annual_maintenance + annual_management)) / purchase_price * 100
        cash_on_cash_return = annual_cash_flow / down_payment * 100 if down_payment > 0 else 0
        
        # Display results
        st.markdown("---")
        st.markdown("## 📊 Investment Analysis Results")
        
        # Key metrics
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.metric("Monthly Cash Flow", f"${monthly_cash_flow:,.2f}", delta=f"${annual_cash_flow:,.0f} annually")
        
        with metric_cols[1]:
            st.metric("Cap Rate", f"{cap_rate:.2f}%", help="Net Operating Income / Purchase Price")
        
        with metric_cols[2]:
            st.metric("Cash-on-Cash Return", f"{cash_on_cash_return:.2f}%", help="Annual Cash Flow / Initial Investment")
        
        with metric_cols[3]:
            total_investment = down_payment + 5000  # Assume $5k closing costs
            roi = annual_cash_flow / total_investment * 100 if total_investment > 0 else 0
            st.metric("ROI", f"{roi:.2f}%", help="Return on Total Investment")
        
        # Detailed breakdown
        st.markdown("### 💰 Financial Breakdown")
        
        breakdown_cols = st.columns(2)
        
        with breakdown_cols[0]:
            st.markdown("**📈 Income**")
            income_data = {
                "Item": ["Gross Annual Rent", "Vacancy Loss", "Effective Annual Rent"],
                "Amount": [f"${annual_rent:,.0f}", f"-${annual_rent * (vacancy_rate/100):,.0f}", f"${effective_annual_rent:,.0f}"]
            }
            st.dataframe(pd.DataFrame(income_data), use_container_width=True, hide_index=True)
        
        with breakdown_cols[1]:
            st.markdown("**📉 Expenses**")
            expense_data = {
                "Item": ["Mortgage Payment", "Property Tax", "Insurance", "Maintenance", "Management", "Total Expenses"],
                "Amount": [f"${annual_mortgage:,.0f}", f"${property_tax:,.0f}", f"${insurance:,.0f}", 
                          f"${annual_maintenance:,.0f}", f"${annual_management:,.0f}", f"${total_annual_expenses:,.0f}"]
            }
            st.dataframe(pd.DataFrame(expense_data), use_container_width=True, hide_index=True)
        
        # Cash flow projection
        st.markdown("### 📈 10-Year Cash Flow Projection")
        
        years = list(range(1, 11))
        projected_rent = [effective_annual_rent * (1 + annual_rent_increase/100)**year for year in range(10)]
        projected_expenses = [total_annual_expenses] * 10  # Simplified - expenses stay constant
        projected_cash_flow = [rent - exp for rent, exp in zip(projected_rent, projected_expenses)]
        cumulative_cash_flow = np.cumsum(projected_cash_flow)
        
        # Create projection chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=years,
            y=projected_cash_flow,
            mode='lines+markers',
            name='Annual Cash Flow',
            line=dict(color='#2E86AB', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=years,
            y=cumulative_cash_flow,
            mode='lines+markers',
            name='Cumulative Cash Flow',
            line=dict(color='#A23B72', width=3),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Cash Flow Projection',
            xaxis_title='Year',
            yaxis_title='Annual Cash Flow ($)',
            yaxis2=dict(
                title='Cumulative Cash Flow ($)',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Investment summary table
        st.markdown("### 📋 Investment Summary")
        
        summary_data = {
            "Metric": [
                "Purchase Price",
                "Down Payment",
                "Loan Amount",
                "Monthly Mortgage Payment",
                "Monthly Rent",
                "Monthly Cash Flow",
                "Annual Cash Flow",
                "Cap Rate",
                "Cash-on-Cash Return",
                "Break-even Occupancy"
            ],
            "Value": [
                f"${purchase_price:,}",
                f"${down_payment:,} ({down_payment_pct}%)",
                f"${loan_amount:,}",
                f"${monthly_payment:,.2f}",
                f"${monthly_rent:,}",
                f"${monthly_cash_flow:,.2f}",
                f"${annual_cash_flow:,.0f}",
                f"{cap_rate:.2f}%",
                f"{cash_on_cash_return:.2f}%",
                f"{(total_annual_expenses / annual_rent * 100):.1f}%"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Save analysis option
        if st.button("💾 Save This Analysis"):
            analysis_data = {
                "type": "property_analysis",
                "property": {
                    "address": address,
                    "purchase_price": purchase_price,
                    "down_payment_pct": down_payment_pct,
                    "loan_term": loan_term,
                    "interest_rate": interest_rate,
                    "monthly_rent": monthly_rent,
                    "vacancy_rate": vacancy_rate,
                    "property_tax": property_tax,
                    "insurance": insurance,
                    "maintenance_pct": maintenance_pct,
                    "management_pct": management_pct
                },
                "results": {
                    "monthly_cash_flow": monthly_cash_flow,
                    "annual_cash_flow": annual_cash_flow,
                    "cap_rate": cap_rate,
                    "cash_on_cash_return": cash_on_cash_return,
                    "roi": roi,
                    "total_investment": total_investment
                },
                "projections": {
                    "years": years,
                    "projected_cash_flow": projected_cash_flow,
                    "cumulative_cash_flow": cumulative_cash_flow.tolist()
                }
            }
            
            result = save_investment_analysis(st.session_state.user.id, analysis_data)
            if result.get("success"):
                st.success("Analysis saved successfully!")
            else:
                st.error(f"Failed to save analysis: {result.get('message')}")

elif analysis_type == "Portfolio Overview":
    st.subheader("📊 Investment Portfolio Overview")
    
    # Load saved analyses
    analyses = get_user_analyses(st.session_state.user.id)
    
    if analyses:
        st.success(f"Found {len(analyses)} saved analyses")
        
        # Portfolio summary metrics
        total_properties = len([a for a in analyses if a.get("analysis_type") == "property_analysis"])
        
        if total_properties > 0:
            # Calculate portfolio totals
            total_investment = 0
            total_annual_cash_flow = 0
            total_purchase_price = 0
            
            portfolio_data = []
            
            for analysis in analyses:
                if analysis.get("analysis_type") == "property_analysis":
                    data = analysis.get("analysis_data", {})
                    property_info = data.get("property", {})
                    results = data.get("results", {})
                    
                    purchase_price = property_info.get("purchase_price", 0)
                    down_payment_pct = property_info.get("down_payment_pct", 20)
                    down_payment = purchase_price * (down_payment_pct / 100)
                    
                    total_investment += down_payment + 5000  # Assume $5k closing costs
                    total_annual_cash_flow += results.get("annual_cash_flow", 0)
                    total_purchase_price += purchase_price
                    
                    portfolio_data.append({
                        "Address": property_info.get("address", "N/A"),
                        "Purchase Price": f"${purchase_price:,}",
                        "Monthly Cash Flow": f"${results.get('monthly_cash_flow', 0):,.2f}",
                        "Cap Rate": f"{results.get('cap_rate', 0):.2f}%",
                        "Cash-on-Cash": f"{results.get('cash_on_cash_return', 0):.2f}%",
                        "Analysis Date": analysis.get("created_at", "")[:10]
                    })
            
            # Portfolio metrics
            portfolio_cols = st.columns(4)
            
            with portfolio_cols[0]:
                st.metric("Total Properties", total_properties)
            
            with portfolio_cols[1]:
                st.metric("Total Investment", f"${total_investment:,.0f}")
            
            with portfolio_cols[2]:
                st.metric("Monthly Cash Flow", f"${total_annual_cash_flow/12:,.2f}")
            
            with portfolio_cols[3]:
                portfolio_roi = (total_annual_cash_flow / total_investment * 100) if total_investment > 0 else 0
                st.metric("Portfolio ROI", f"{portfolio_roi:.2f}%")
            
            # Portfolio table
            st.markdown("### 📋 Portfolio Properties")
            portfolio_df = pd.DataFrame(portfolio_data)
            st.dataframe(portfolio_df, use_container_width=True, hide_index=True)
            
            # Portfolio performance chart
            if len(portfolio_data) > 1:
                st.markdown("### 📈 Portfolio Performance")
                
                # Extract cash flow data for chart
                addresses = [row["Address"][:30] + "..." if len(row["Address"]) > 30 else row["Address"] for row in portfolio_data]
                cash_flows = [float(row["Monthly Cash Flow"].replace("$", "").replace(",", "")) for row in portfolio_data]
                
                fig = px.bar(
                    x=addresses,
                    y=cash_flows,
                    title="Monthly Cash Flow by Property",
                    labels={"x": "Property", "y": "Monthly Cash Flow ($)"}
                )
                
                fig.update_layout(
                    xaxis_tickangle=-45,
                    template='plotly_white'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("No property analyses found in your portfolio.")
    
    else:
        st.info("No saved analyses found. Analyze some properties first to see your portfolio overview.")

elif analysis_type == "Market Comparison":
    st.subheader("🏘️ Market Comparison Analysis")
    
    # Load properties from searches for comparison
    properties = load_property_from_searches(st.session_state.user.id)
    
    if len(properties) > 1:
        st.success(f"Found {len(properties)} properties for comparison")
        
        # Create comparison dataframe
        comparison_data = []
        for prop in properties:
            comparison_data.append({
                "Address": prop.get("address", "N/A"),
                "Property Type": prop.get("property_type", "N/A"),
                "Bedrooms": prop.get("bedrooms", 0),
                "Bathrooms": prop.get("bathrooms", 0),
                "Square Footage": prop.get("square_footage", 0),
                "Year Built": prop.get("year_built", 0),
                "Last Sale Price": prop.get("last_sale_price", 0),
                "Price per Sq Ft": prop.get("last_sale_price", 0) / prop.get("square_footage", 1) if prop.get("square_footage", 0) > 0 else 0,
                "County": prop.get("county", "N/A"),
                "State": prop.get("state", "N/A"),
                "Property Tax": prop.get("annual_property_tax", 0)
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Filter options
        filter_cols = st.columns(3)
        
        with filter_cols[0]:
            property_types = comparison_df["Property Type"].unique().tolist()
            selected_types = st.multiselect("Filter by Property Type", property_types, default=property_types)
        
        with filter_cols[1]:
            min_price = st.number_input("Min Price", min_value=0, value=0)
            max_price = st.number_input("Max Price", min_value=0, value=int(comparison_df["Last Sale Price"].max()) if comparison_df["Last Sale Price"].max() > 0 else 1000000)
        
        with filter_cols[2]:
            counties = comparison_df["County"].unique().tolist()
            selected_counties = st.multiselect("Filter by County", counties, default=counties)
        
        # Apply filters
        filtered_df = comparison_df[
            (comparison_df["Property Type"].isin(selected_types)) &
            (comparison_df["Last Sale Price"] >= min_price) &
            (comparison_df["Last Sale Price"] <= max_price) &
            (comparison_df["County"].isin(selected_counties))
        ]
        
        if not filtered_df.empty:
            # Market statistics
            st.markdown("### 📊 Market Statistics")
            
            stats_cols = st.columns(4)
            
            with stats_cols[0]:
                avg_price = filtered_df["Last Sale Price"].mean()
                st.metric("Average Price", f"${avg_price:,.0f}")
            
            with stats_cols[1]:
                median_price = filtered_df["Last Sale Price"].median()
                st.metric("Median Price", f"${median_price:,.0f}")
            
            with stats_cols[2]:
                avg_price_per_sqft = filtered_df["Price per Sq Ft"].mean()
                st.metric("Avg Price/Sq Ft", f"${avg_price_per_sqft:.2f}")
            
            with stats_cols[3]:
                avg_tax = filtered_df["Property Tax"].mean()
                st.metric("Avg Property Tax", f"${avg_tax:,.0f}")
            
            # Price distribution
            st.markdown("### 📈 Price Distribution")
            
            fig = px.histogram(
                filtered_df,
                x="Last Sale Price",
                nbins=20,
                title="Property Price Distribution"
            )
            
            fig.update_layout(template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
            
            # Price vs Square Footage scatter
            st.markdown("### 🏠 Price vs Square Footage")
            
            fig = px.scatter(
                filtered_df,
                x="Square Footage",
                y="Last Sale Price",
                color="Property Type",
                size="Bedrooms",
                hover_data=["Address", "Year Built"],
                title="Price vs Square Footage by Property Type"
            )
            
            fig.update_layout(template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
            
            # Comparison table
            st.markdown("### 📋 Property Comparison Table")
            
            # Format the dataframe for display
            display_df = filtered_df.copy()
            display_df["Last Sale Price"] = display_df["Last Sale Price"].apply(lambda x: f"${x:,.0f}" if x > 0 else "N/A")
            display_df["Price per Sq Ft"] = display_df["Price per Sq Ft"].apply(lambda x: f"${x:.2f}" if x > 0 else "N/A")
            display_df["Property Tax"] = display_df["Property Tax"].apply(lambda x: f"${x:,.0f}" if x > 0 else "N/A")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        else:
            st.warning("No properties match the selected filters.")
    
    else:
        st.info("Need at least 2 properties for comparison. Search for more properties first.")

elif analysis_type == "Scenario Planning":
    st.subheader("🎯 Investment Scenario Planning")
    
    st.markdown("Analyze different investment scenarios and market conditions.")
    
    # Scenario parameters
    scenario_cols = st.columns(2)
    
    with scenario_cols[0]:
        st.markdown("#### 📊 Base Scenario")
        base_purchase_price = st.number_input("Purchase Price ($)", min_value=0, value=300000, key="base_price")
        base_rent = st.number_input("Monthly Rent ($)", min_value=0, value=2500, key="base_rent")
        base_appreciation = st.slider("Annual Appreciation (%)", min_value=-10, max_value=20, value=3, key="base_appreciation")
    
    with scenario_cols[1]:
        st.markdown("#### 🎯 Scenario Variations")
        price_variation = st.slider("Purchase Price Variation (%)", min_value=-50, max_value=50, value=0)
        rent_variation = st.slider("Rent Variation (%)", min_value=-50, max_value=50, value=0)
        appreciation_variation = st.slider("Appreciation Variation (%)", min_value=-10, max_value=10, value=0)
    
    # Calculate scenarios
    scenarios = {
        "Conservative": {
            "purchase_price": base_purchase_price * 1.1,  # 10% higher price
            "monthly_rent": base_rent * 0.9,  # 10% lower rent
            "appreciation": base_appreciation - 1  # 1% lower appreciation
        },
        "Base Case": {
            "purchase_price": base_purchase_price,
            "monthly_rent": base_rent,
            "appreciation": base_appreciation
        },
        "Optimistic": {
            "purchase_price": base_purchase_price * 0.9,  # 10% lower price
            "monthly_rent": base_rent * 1.1,  # 10% higher rent
            "appreciation": base_appreciation + 1  # 1% higher appreciation
        },
        "Custom": {
            "purchase_price": base_purchase_price * (1 + price_variation/100),
            "monthly_rent": base_rent * (1 + rent_variation/100),
            "appreciation": base_appreciation + appreciation_variation
        }
    }
    
    # Calculate returns for each scenario
    st.markdown("### 📊 Scenario Comparison")
    
    scenario_results = []
    
    for scenario_name, params in scenarios.items():
        # Basic calculations (simplified)
        purchase_price = params["purchase_price"]
        monthly_rent = params["monthly_rent"]
        annual_rent = monthly_rent * 12
        
        # Assume 20% down payment, 6.5% interest, 30-year loan
        down_payment = purchase_price * 0.2
        loan_amount = purchase_price - down_payment
        monthly_payment = loan_amount * 0.00542  # Approximate payment factor
        
        # Assume expenses are 40% of rent
        annual_expenses = annual_rent * 0.4 + (monthly_payment * 12)
        annual_cash_flow = annual_rent - annual_expenses
        
        # 10-year projection
        property_value_10yr = purchase_price * (1 + params["appreciation"]/100)**10
        total_appreciation = property_value_10yr - purchase_price
        
        # Total return
        total_cash_flow_10yr = annual_cash_flow * 10  # Simplified
        total_return = total_cash_flow_10yr + total_appreciation
        roi = (total_return / down_payment) * 100 if down_payment > 0 else 0
        
        scenario_results.append({
            "Scenario": scenario_name,
            "Purchase Price": f"${purchase_price:,.0f}",
            "Monthly Rent": f"${monthly_rent:,.0f}",
            "Annual Cash Flow": f"${annual_cash_flow:,.0f}",
            "10-Year Property Value": f"${property_value_10yr:,.0f}",
            "Total 10-Year Return": f"${total_return:,.0f}",
            "ROI (10-year)": f"{roi:.1f}%"
        })
    
    scenario_df = pd.DataFrame(scenario_results)
    st.dataframe(scenario_df, use_container_width=True, hide_index=True)
    
    # Scenario comparison chart
    st.markdown("### 📈 ROI Comparison")
    
    roi_values = [float(row["ROI (10-year)"].replace("%", "")) for row in scenario_results]
    scenario_names = [row["Scenario"] for row in scenario_results]
    
    fig = px.bar(
        x=scenario_names,
        y=roi_values,
        title="10-Year ROI by Scenario",
        labels={"x": "Scenario", "y": "ROI (%)"},
        color=roi_values,
        color_continuous_scale="RdYlGn"
    )
    
    fig.update_layout(template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk analysis
    st.markdown("### ⚠️ Risk Analysis")
    
    risk_cols = st.columns(2)
    
    with risk_cols[0]:
        st.markdown("**Market Risks:**")
        st.write("• Interest rate changes")
        st.write("• Property value fluctuations")
        st.write("• Rental market conditions")
        st.write("• Economic downturns")
    
    with risk_cols[1]:
        st.markdown("**Property-Specific Risks:**")
        st.write("• Vacancy periods")
        st.write("• Maintenance and repairs")
        st.write("• Property management issues")
        st.write("• Neighborhood changes")

# Footer with additional tools
st.markdown("---")
st.markdown("### 🔧 Additional Tools")

tool_cols = st.columns(4)

with tool_cols[0]:
    if st.button("📊 Export Analysis", use_container_width=True):
        st.info("Export functionality coming soon!")

with tool_cols[1]:
    if st.button("📧 Email Report", use_container_width=True):
        st.info("Email functionality coming soon!")

with tool_cols[2]:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

with tool_cols[3]:
    if st.button("❓ Help & Guide", use_container_width=True):
        st.info("Help documentation coming soon!")

