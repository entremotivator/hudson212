import streamlit as st
import json
from datetime import datetime
from utils.auth import initialize_auth_state, login_user, register_user, logout_user, enable_demo_mode
from utils.search_database import save_property_search, initialize_demo_data

# Page configuration
st.set_page_config(
    page_title="Property Investment Platform",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize auth state
initialize_auth_state()

# Custom CSS for light blue theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #87CEEB 0%, #4682B4 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .feature-card {
        background: #F0F8FF;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #4682B4;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #E6F3FF 0%, #CCE7FF 100%);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .sidebar .sidebar-content {
        background: #F8FBFF;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #4682B4 0%, #87CEEB 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #2E5984 0%, #6BB6FF 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Main app logic
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏠 Property Investment Platform</h1>
        <p>Comprehensive real estate search, analysis, and investment tools</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check authentication status
    if st.session_state.user is None:
        show_auth_page()
    else:
        show_main_app()

def show_auth_page():
    """Display authentication page"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Welcome to Property Investment Platform")
        
        # Demo mode option
        st.markdown("---")
        st.markdown("#### 🎯 Quick Demo")
        st.markdown("Try the platform without creating an account:")
        
        if st.button("🚀 Enter Demo Mode", use_container_width=True, type="primary"):
            enable_demo_mode()
            initialize_demo_data()
            st.success("Demo mode activated! You can now explore all features.")
            st.rerun()
        
        st.markdown("---")
        
        # Authentication tabs
        auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with auth_tab1:
            with st.form("login_form"):
                st.markdown("#### Login to Your Account")
                email = st.text_input("Email", placeholder="your.email@example.com")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("🔑 Login", use_container_width=True):
                    if email and password:
                        result = login_user(email, password)
                        if result.get("success"):
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error(f"Login failed: {result.get('message')}")
                    else:
                        st.error("Please enter both email and password.")
        
        with auth_tab2:
            with st.form("register_form"):
                st.markdown("#### Create New Account")
                reg_email = st.text_input("Email", placeholder="your.email@example.com", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                reg_password_confirm = st.text_input("Confirm Password", type="password")
                full_name = st.text_input("Full Name", placeholder="John Doe")
                
                if st.form_submit_button("📝 Create Account", use_container_width=True):
                    if reg_email and reg_password and reg_password_confirm:
                        if reg_password == reg_password_confirm:
                            result = register_user(reg_email, reg_password, full_name)
                            if result.get("success"):
                                st.success(result.get("message"))
                            else:
                                st.error(f"Registration failed: {result.get('message')}")
                        else:
                            st.error("Passwords do not match.")
                    else:
                        st.error("Please fill in all required fields.")
        
        # Platform features
        st.markdown("---")
        st.markdown("### ✨ Platform Features")
        
        features = [
            {"icon": "🔍", "title": "Property Search", "desc": "Search and analyze properties with comprehensive data"},
            {"icon": "📊", "title": "Investment Analysis", "desc": "Calculate ROI, cash flow, and investment metrics"},
            {"icon": "📋", "title": "Search Management", "desc": "Save, organize, and track your property searches"},
            {"icon": "📈", "title": "Portfolio Overview", "desc": "Monitor your investment portfolio performance"},
            {"icon": "🏘️", "title": "Market Comparison", "desc": "Compare properties and analyze market trends"},
            {"icon": "🎯", "title": "Scenario Planning", "desc": "Model different investment scenarios and outcomes"}
        ]
        
        for i in range(0, len(features), 2):
            col1, col2 = st.columns(2)
            
            with col1:
                if i < len(features):
                    feature = features[i]
                    st.markdown(f"""
                    <div class="feature-card">
                        <h4>{feature['icon']} {feature['title']}</h4>
                        <p>{feature['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                if i + 1 < len(features):
                    feature = features[i + 1]
                    st.markdown(f"""
                    <div class="feature-card">
                        <h4>{feature['icon']} {feature['title']}</h4>
                        <p>{feature['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True)

def show_main_app():
    """Display main application interface"""
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 👤 User Account")
        user_email = st.session_state.user.email
        st.markdown(f"**Logged in as:** {user_email}")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()
        
        st.markdown("---")
        
        # Navigation menu
        st.markdown("### 🧭 Navigation")
        
        # Property search section
        if st.button("🔍 Property Search", use_container_width=True):
            st.session_state.current_page = "search"
        
        if st.button("📋 Saved Searches", use_container_width=True):
            st.session_state.current_page = "saved_searches"
        
        if st.button("📊 Investment Analysis", use_container_width=True):
            st.session_state.current_page = "investment_analysis"
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("📥 Import Property Data", use_container_width=True):
            st.session_state.show_import_modal = True
        
        if st.button("📈 Generate Report", use_container_width=True):
            st.session_state.show_report_modal = True
    
    # Main content area
    current_page = st.session_state.get("current_page", "dashboard")
    
    if current_page == "dashboard":
        show_dashboard()
    elif current_page == "search":
        show_property_search()
    elif current_page == "saved_searches":
        # Import the saved searches page
        exec(open("pages/saved_searches.py").read())
    elif current_page == "investment_analysis":
        # Import the investment analysis page
        exec(open("pages/investment_analysis.py").read())
    
    # Handle modals
    if st.session_state.get("show_import_modal"):
        show_import_modal()
    
    if st.session_state.get("show_report_modal"):
        show_report_modal()

def show_dashboard():
    """Display main dashboard"""
    
    st.markdown("## 🏠 Dashboard")
    st.markdown("Welcome to your property investment platform. Get started by exploring the features below.")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🔍</h3>
            <h4>Property Search</h4>
            <p>Find and analyze properties</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Start Searching", key="dash_search", use_container_width=True):
            st.session_state.current_page = "search"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📋</h3>
            <h4>Saved Searches</h4>
            <p>Manage your search history</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("View Searches", key="dash_saved", use_container_width=True):
            st.session_state.current_page = "saved_searches"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📊</h3>
            <h4>Investment Analysis</h4>
            <p>Calculate investment metrics</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Analyze Properties", key="dash_analysis", use_container_width=True):
            st.session_state.current_page = "investment_analysis"
            st.rerun()
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>📈</h3>
            <h4>Portfolio</h4>
            <p>Track your investments</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("View Portfolio", key="dash_portfolio", use_container_width=True):
            st.session_state.current_page = "investment_analysis"
            st.rerun()
    
    # Recent activity section
    st.markdown("---")
    st.markdown("### 📊 Platform Overview")
    
    overview_col1, overview_col2 = st.columns(2)
    
    with overview_col1:
        st.markdown("""
        #### 🎯 Getting Started
        
        1. **Search for Properties**: Use our comprehensive property search to find investment opportunities
        2. **Analyze Investments**: Calculate cash flow, ROI, and other key metrics
        3. **Save Your Searches**: Keep track of properties you're interested in
        4. **Compare Options**: Use our comparison tools to evaluate multiple properties
        5. **Plan Scenarios**: Model different investment scenarios and market conditions
        """)
    
    with overview_col2:
        st.markdown("""
        #### 🔧 Key Features
        
        - **Comprehensive Property Data**: Access detailed property information including tax history, features, and ownership details
        - **Advanced Investment Calculations**: Calculate cap rates, cash-on-cash returns, and long-term projections
        - **Portfolio Management**: Track multiple properties and analyze portfolio performance
        - **Market Analysis**: Compare properties and analyze market trends
        - **Export Capabilities**: Download your analyses in multiple formats (JSON, CSV, Excel)
        """)
    
    # Sample data showcase
    st.markdown("---")
    st.markdown("### 📋 Sample Property Data")
    st.markdown("Here's an example of the detailed property information available in our platform:")
    
    # Load sample data from the uploaded JSON
    try:
        with open("/home/ubuntu/upload/property_search_28_20250828_035827.json", 'r') as f:
            sample_data = json.load(f)
        
        if sample_data.get("results"):
            sample_prop = sample_data["results"][0]
            
            sample_col1, sample_col2, sample_col3 = st.columns(3)
            
            with sample_col1:
                st.markdown("**Basic Information**")
                st.write(f"Address: {sample_prop.get('formattedAddress', 'N/A')}")
                st.write(f"Property Type: {sample_prop.get('propertyType', 'N/A')}")
                st.write(f"Bedrooms: {sample_prop.get('bedrooms', 'N/A')}")
                st.write(f"Bathrooms: {sample_prop.get('bathrooms', 'N/A')}")
                st.write(f"Square Footage: {sample_prop.get('squareFootage', 'N/A'):,}" if sample_prop.get('squareFootage') else "Square Footage: N/A")
            
            with sample_col2:
                st.markdown("**Financial Information**")
                st.write(f"Last Sale Price: ${sample_prop.get('lastSalePrice', 0):,}" if sample_prop.get('lastSalePrice') else "Last Sale Price: N/A")
                st.write(f"Year Built: {sample_prop.get('yearBuilt', 'N/A')}")
                st.write(f"Lot Size: {sample_prop.get('lotSize', 'N/A'):,} sq ft" if sample_prop.get('lotSize') else "Lot Size: N/A")
                st.write(f"County: {sample_prop.get('county', 'N/A')}")
                st.write(f"Zoning: {sample_prop.get('zoning', 'N/A')}")
            
            with sample_col3:
                st.markdown("**Tax Information**")
                tax_assessments = sample_prop.get('taxAssessments', {})
                if tax_assessments:
                    latest_year = max(tax_assessments.keys())
                    latest_assessment = tax_assessments[latest_year]
                    st.write(f"Assessed Value ({latest_year}): ${latest_assessment.get('value', 0):,}")
                    st.write(f"Land Value: ${latest_assessment.get('land', 0):,}")
                    st.write(f"Improvement Value: ${latest_assessment.get('improvements', 0):,}")
                
                property_taxes = sample_prop.get('propertyTaxes', {})
                if property_taxes:
                    latest_tax_year = max(property_taxes.keys())
                    st.write(f"Property Tax ({latest_tax_year}): ${property_taxes[latest_tax_year].get('total', 0):,}")
    
    except Exception as e:
        st.info("Sample property data will be available after you perform your first search.")

def show_property_search():
    """Display property search interface"""
    
    st.markdown("## 🔍 Property Search")
    st.markdown("Search for properties and save the results for analysis.")
    
    # Search form
    with st.form("property_search_form"):
        search_col1, search_col2 = st.columns([2, 1])
        
        with search_col1:
            address = st.text_input("Property Address", placeholder="Enter address, city, or ZIP code")
        
        with search_col2:
            search_button = st.form_submit_button("🔍 Search Properties", use_container_width=True)
    
    if search_button and address:
        # Simulate property search (in real implementation, this would call an API)
        st.info("🔄 Searching for properties... (This is a demo - in production, this would call a real property API)")
        
        # For demo purposes, use the sample data
        try:
            with open("/home/ubuntu/upload/property_search_28_20250828_035827.json", 'r') as f:
                sample_data = json.load(f)
            
            # Save the search
            search_params = {"address": address}
            result = save_property_search(st.session_state.user.id, sample_data, search_params)
            
            if result.get("success"):
                st.success(f"✅ Search completed and saved! Found {len(sample_data.get('results', []))} property(ies).")
                
                # Display results
                if sample_data.get("results"):
                    for i, prop in enumerate(sample_data["results"]):
                        with st.expander(f"🏠 {prop.get('formattedAddress', 'Property')} - ${prop.get('lastSalePrice', 0):,}" if prop.get('lastSalePrice') else f"🏠 {prop.get('formattedAddress', 'Property')}", expanded=i==0):
                            
                            # Property details
                            prop_col1, prop_col2, prop_col3 = st.columns(3)
                            
                            with prop_col1:
                                st.markdown("**Basic Info**")
                                st.write(f"Type: {prop.get('propertyType', 'N/A')}")
                                st.write(f"Bedrooms: {prop.get('bedrooms', 'N/A')}")
                                st.write(f"Bathrooms: {prop.get('bathrooms', 'N/A')}")
                                st.write(f"Square Footage: {prop.get('squareFootage', 'N/A'):,}" if prop.get('squareFootage') else "Square Footage: N/A")
                            
                            with prop_col2:
                                st.markdown("**Location**")
                                st.write(f"County: {prop.get('county', 'N/A')}")
                                st.write(f"State: {prop.get('state', 'N/A')}")
                                st.write(f"ZIP: {prop.get('zipCode', 'N/A')}")
                                st.write(f"Zoning: {prop.get('zoning', 'N/A')}")
                            
                            with prop_col3:
                                st.markdown("**Financial**")
                                st.write(f"Last Sale: ${prop.get('lastSalePrice', 0):,}" if prop.get('lastSalePrice') else "Last Sale: N/A")
                                st.write(f"Year Built: {prop.get('yearBuilt', 'N/A')}")
                                st.write(f"Lot Size: {prop.get('lotSize', 'N/A'):,} sq ft" if prop.get('lotSize') else "Lot Size: N/A")
                                st.write(f"Owner Occupied: {'Yes' if prop.get('ownerOccupied') else 'No'}")
                            
                            # Quick analysis button
                            if st.button(f"📊 Analyze Investment Potential", key=f"analyze_{i}"):
                                st.session_state.current_page = "investment_analysis"
                                st.session_state.selected_property = prop
                                st.rerun()
                
                st.markdown("---")
                st.markdown("💡 **Tip**: Go to 'Saved Searches' to view detailed information and download your search results.")
            
            else:
                st.error(f"Failed to save search: {result.get('message')}")
        
        except Exception as e:
            st.error(f"Search failed: {str(e)}")
    
    # Search tips
    st.markdown("---")
    st.markdown("### 💡 Search Tips")
    
    tip_col1, tip_col2 = st.columns(2)
    
    with tip_col1:
        st.markdown("""
        **Address Formats:**
        - Full address: "123 Main St, City, State ZIP"
        - City and state: "Atlanta, GA"
        - ZIP code: "30309"
        - Neighborhood: "Buckhead, Atlanta"
        """)
    
    with tip_col2:
        st.markdown("""
        **What You'll Get:**
        - Property details and features
        - Tax assessment history
        - Sale history and pricing
        - Owner information
        - Investment analysis tools
        """)

def show_import_modal():
    """Display import data modal"""
    
    st.markdown("### 📥 Import Property Data")
    
    uploaded_file = st.file_uploader("Upload Property Data", type=['json', 'csv'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.type == "application/json":
                data = json.load(uploaded_file)
                st.success("JSON file uploaded successfully!")
                
                # Save the imported data
                result = save_property_search(st.session_state.user.id, data, {"source": "import"})
                if result.get("success"):
                    st.success("Data imported and saved successfully!")
                else:
                    st.error(f"Failed to save imported data: {result.get('message')}")
            
            elif uploaded_file.type == "text/csv":
                st.info("CSV import functionality coming soon!")
            
        except Exception as e:
            st.error(f"Import failed: {str(e)}")
    
    if st.button("Close"):
        st.session_state.show_import_modal = False
        st.rerun()

def show_report_modal():
    """Display report generation modal"""
    
    st.markdown("### 📈 Generate Report")
    
    report_type = st.selectbox("Report Type", [
        "Property Analysis Summary",
        "Portfolio Performance Report",
        "Market Comparison Report",
        "Investment Projections"
    ])
    
    report_format = st.selectbox("Format", ["PDF", "Excel", "CSV"])
    
    if st.button("Generate Report"):
        st.info(f"Generating {report_type} in {report_format} format... (Feature coming soon!)")
    
    if st.button("Close", key="close_report"):
        st.session_state.show_report_modal = False
        st.rerun()

if __name__ == "__main__":
    main()

