import streamlit as st
import json
import pandas as pd
import requests
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io

# --------------------------
# Page configuration
# --------------------------
st.set_page_config(
    page_title="Ohio Property Tax Lookup Pro - AI PropIQ",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# Hide Streamlit elements and add custom CSS
# --------------------------
hide_streamlit_style = """
<style>
    /* Hide main menu */
    #MainMenu {visibility: hidden;}
    
    /* Hide footer */
    footer {visibility: hidden;}
    
    /* Hide header */
    header {visibility: hidden;}
    
    /* Hide deploy button */
    .stDeployButton {display:none;}
    
    /* Hide "Made with Streamlit" */
    .stApp > footer {visibility: hidden;}
    
    /* Hide hamburger menu */
    .st-emotion-cache-1629p8f {display: none;}
    
    /* Hide fullscreen button on charts/dataframes */
    button[title="View fullscreen"] {
        visibility: hidden;
    }
    
    /* Custom styling for better appearance */
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Hide settings menu */
    .stActionButton {display: none;}
    
    /* Custom footer */
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        color: white;
        text-align: center;
        padding: 10px 0;
        z-index: 999;
    }
    
    /* Premium link styling - Light Blue Theme */
    .premium-link {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        padding: 15px 20px;
        border-radius: 10px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(33,150,243,0.3);
    }
    
    .premium-link a {
        color: white !important;
        text-decoration: none !important;
        font-weight: bold;
        font-size: 16px;
    }
    
    .premium-link a:hover {
        text-decoration: underline !important;
    }
    
    /* Address highlight styling */
    .address-highlight {
        background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 6px 20px rgba(25,118,210,0.4);
        text-align: center;
    }
    
    .address-highlight h3 {
        color: white;
        margin-bottom: 15px;
        font-size: 24px;
    }
    
    .address-text {
        font-size: 18px;
        font-weight: bold;
        margin: 8px 0;
    }
    
    /* Mailing address styling */
    .mailing-address {
        background: linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 12px rgba(66,165,245,0.3);
    }
    
    .mailing-address h4 {
        color: white;
        margin-bottom: 10px;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --------------------------
# Complete Ohio Counties Configuration (All 88 Counties)
# --------------------------
OHIO_COUNTIES = {
    '01': {'code': '01', 'name': 'Adams County', 'seat': 'West Union'},
    '02': {'code': '02', 'name': 'Allen County', 'seat': 'Lima'},
    '03': {'code': '03', 'name': 'Ashland County', 'seat': 'Ashland'},
    '04': {'code': '04', 'name': 'Ashtabula County', 'seat': 'Jefferson'},
    '05': {'code': '05', 'name': 'Athens County', 'seat': 'Athens'},
    '06': {'code': '06', 'name': 'Auglaize County', 'seat': 'Wapakoneta'},
    '07': {'code': '07', 'name': 'Belmont County', 'seat': 'St. Clairsville'},
    '08': {'code': '08', 'name': 'Brown County', 'seat': 'Georgetown'},
    '09': {'code': '09', 'name': 'Butler County', 'seat': 'Hamilton'},
    '10': {'code': '10', 'name': 'Carroll County', 'seat': 'Carrollton'},
    '11': {'code': '11', 'name': 'Champaign County', 'seat': 'Urbana'},
    '12': {'code': '12', 'name': 'Clark County', 'seat': 'Springfield'},
    '13': {'code': '13', 'name': 'Clermont County', 'seat': 'Batavia'},
    '14': {'code': '14', 'name': 'Clinton County', 'seat': 'Wilmington'},
    '15': {'code': '15', 'name': 'Columbiana County', 'seat': 'Lisbon'},
    '16': {'code': '16', 'name': 'Coshocton County', 'seat': 'Coshocton'},
    '17': {'code': '17', 'name': 'Crawford County', 'seat': 'Bucyrus'},
    '18': {'code': '18', 'name': 'Cuyahoga County', 'seat': 'Cleveland'},
    '19': {'code': '19', 'name': 'Darke County', 'seat': 'Greenville'},
    '20': {'code': '20', 'name': 'Defiance County', 'seat': 'Defiance'},
    '21': {'code': '21', 'name': 'Delaware County', 'seat': 'Delaware'},
    '22': {'code': '22', 'name': 'Erie County', 'seat': 'Sandusky'},
    '23': {'code': '23', 'name': 'Fairfield County', 'seat': 'Lancaster'},
    '24': {'code': '24', 'name': 'Fayette County', 'seat': 'Washington Court House'},
    '25': {'code': '25', 'name': 'Franklin County', 'seat': 'Columbus'},
    '26': {'code': '26', 'name': 'Fulton County', 'seat': 'Wauseon'},
    '27': {'code': '27', 'name': 'Gallia County', 'seat': 'Gallipolis'},
    '28': {'code': '28', 'name': 'Geauga County', 'seat': 'Chardon'},
    '29': {'code': '29', 'name': 'Greene County', 'seat': 'Xenia'},
    '30': {'code': '30', 'name': 'Guernsey County', 'seat': 'Cambridge'},
    '31': {'code': '31', 'name': 'Hamilton County', 'seat': 'Cincinnati'},
    '32': {'code': '32', 'name': 'Hancock County', 'seat': 'Findlay'},
    '33': {'code': '33', 'name': 'Hardin County', 'seat': 'Kenton'},
    '34': {'code': '34', 'name': 'Harrison County', 'seat': 'Cadiz'},
    '35': {'code': '35', 'name': 'Henry County', 'seat': 'Napoleon'},
    '36': {'code': '36', 'name': 'Highland County', 'seat': 'Hillsboro'},
    '37': {'code': '37', 'name': 'Hocking County', 'seat': 'Logan'},
    '38': {'code': '38', 'name': 'Holmes County', 'seat': 'Millersburg'},
    '39': {'code': '39', 'name': 'Huron County', 'seat': 'Norwalk'},
    '40': {'code': '40', 'name': 'Jackson County', 'seat': 'Jackson'},
    '41': {'code': '41', 'name': 'Jefferson County', 'seat': 'Steubenville'},
    '42': {'code': '42', 'name': 'Knox County', 'seat': 'Mount Vernon'},
    '43': {'code': '43', 'name': 'Lake County', 'seat': 'Painesville'},
    '44': {'code': '44', 'name': 'Lawrence County', 'seat': 'Ironton'},
    '45': {'code': '45', 'name': 'Licking County', 'seat': 'Newark'},
    '46': {'code': '46', 'name': 'Logan County', 'seat': 'Bellefontaine'},
    '47': {'code': '47', 'name': 'Lorain County', 'seat': 'Elyria'},
    '48': {'code': '48', 'name': 'Lucas County', 'seat': 'Toledo'},
    '49': {'code': '49', 'name': 'Madison County', 'seat': 'London'},
    '50': {'code': '50', 'name': 'Mahoning County', 'seat': 'Youngstown'},
    '51': {'code': '51', 'name': 'Marion County', 'seat': 'Marion'},
    '52': {'code': '52', 'name': 'Medina County', 'seat': 'Medina'},
    '53': {'code': '53', 'name': 'Meigs County', 'seat': 'Pomeroy'},
    '54': {'code': '54', 'name': 'Mercer County', 'seat': 'Celina'},
    '55': {'code': '55', 'name': 'Miami County', 'seat': 'Troy'},
    '56': {'code': '56', 'name': 'Monroe County', 'seat': 'Woodsfield'},
    '57': {'code': '57', 'name': 'Montgomery County', 'seat': 'Dayton'},
    '58': {'code': '58', 'name': 'Morgan County', 'seat': 'McConnelsville'},
    '59': {'code': '59', 'name': 'Morrow County', 'seat': 'Mount Gilead'},
    '60': {'code': '60', 'name': 'Muskingum County', 'seat': 'Zanesville'},
    '61': {'code': '61', 'name': 'Noble County', 'seat': 'Caldwell'},
    '62': {'code': '62', 'name': 'Ottawa County', 'seat': 'Port Clinton'},
    '63': {'code': '63', 'name': 'Paulding County', 'seat': 'Paulding'},
    '64': {'code': '64', 'name': 'Perry County', 'seat': 'New Lexington'},
    '65': {'code': '65', 'name': 'Pickaway County', 'seat': 'Circleville'},
    '66': {'code': '66', 'name': 'Pike County', 'seat': 'Waverly'},
    '67': {'code': '67', 'name': 'Portage County', 'seat': 'Ravenna'},
    '68': {'code': '68', 'name': 'Preble County', 'seat': 'Eaton'},
    '69': {'code': '69', 'name': 'Putnam County', 'seat': 'Ottawa'},
    '70': {'code': '70', 'name': 'Richland County', 'seat': 'Mansfield'},
    '71': {'code': '71', 'name': 'Ross County', 'seat': 'Chillicothe'},
    '72': {'code': '72', 'name': 'Sandusky County', 'seat': 'Fremont'},
    '73': {'code': '73', 'name': 'Scioto County', 'seat': 'Portsmouth'},
    '74': {'code': '74', 'name': 'Seneca County', 'seat': 'Tiffin'},
    '75': {'code': '75', 'name': 'Shelby County', 'seat': 'Sidney'},
    '76': {'code': '76', 'name': 'Stark County', 'seat': 'Canton'},
    '77': {'code': '77', 'name': 'Summit County', 'seat': 'Akron'},
    '78': {'code': '78', 'name': 'Trumbull County', 'seat': 'Warren'},
    '79': {'code': '79', 'name': 'Tuscarawas County', 'seat': 'New Philadelphia'},
    '80': {'code': '80', 'name': 'Union County', 'seat': 'Marysville'},
    '81': {'code': '81', 'name': 'Van Wert County', 'seat': 'Van Wert'},
    '82': {'code': '82', 'name': 'Vinton County', 'seat': 'McArthur'},
    '83': {'code': '83', 'name': 'Warren County', 'seat': 'Lebanon'},
    '84': {'code': '84', 'name': 'Washington County', 'seat': 'Marietta'},
    '85': {'code': '85', 'name': 'Wayne County', 'seat': 'Wooster'},
    '86': {'code': '86', 'name': 'Williams County', 'seat': 'Bryan'},
    '87': {'code': '87', 'name': 'Wood County', 'seat': 'Bowling Green'},
    '88': {'code': '88', 'name': 'Wyandot County', 'seat': 'Upper Sandusky'}
}

# --------------------------
# Real Property Data API Configuration - ReportAllUSA (Keep API stuff the same)
# --------------------------
PROPERTY_API_CONFIG = {
    "REPORTALLUSA_CLIENT_KEY": st.secrets.get("reportallusa", {}).get("client", ""),
    "REPORTALLUSA_BASE_URL": "https://reportallusa.com/api/parcels",
    "API_VERSION": "9"
}

# --------------------------
# Enhanced Session State Management
# --------------------------
def initialize_session_state():
    """Initialize all session state variables for better app data persistence"""
    if 'usage_count' not in st.session_state:
        st.session_state.usage_count = 0
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'cached_results' not in st.session_state:
        st.session_state.cached_results = {}
    if 'all_search_results' not in st.session_state:
        st.session_state.all_search_results = []
    if 'current_property_data' not in st.session_state:
        st.session_state.current_property_data = None
    if 'last_search_timestamp' not in st.session_state:
        st.session_state.last_search_timestamp = None
    if 'app_session_id' not in st.session_state:
        st.session_state.app_session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

def add_search_to_history(parcel_id, county_filter, results):
    """Add search results to session history for combined PDF generation"""
    search_entry = {
        'timestamp': datetime.now(),
        'parcel_id': parcel_id,
        'county_filter': county_filter,
        'results': results,
        'search_id': len(st.session_state.all_search_results) + 1
    }
    st.session_state.all_search_results.append(search_entry)
    st.session_state.current_property_data = results[0] if results else None
    st.session_state.last_search_timestamp = datetime.now()

# --------------------------
# Enhanced API Functions for Real Ohio Property Data - ReportAllUSA (Keep API same)
# --------------------------
def fetch_ohio_property_data_reportallusa(parcel_id, county_name=None):
    """
    Fetch property data using ReportAllUSA API for Ohio state-wide search
    """
    try:
        client_key = PROPERTY_API_CONFIG["REPORTALLUSA_CLIENT_KEY"]
        if not client_key:
            return {
                "status": "ERROR", 
                "message": "API client key not configured. Please set client key in configuration.",
                "raw_response": None
            }

        base_url = PROPERTY_API_CONFIG["REPORTALLUSA_BASE_URL"]
        api_version = PROPERTY_API_CONFIG["API_VERSION"]
        
        # Build search parameters for Ohio state-wide search
        params = {
            'client': client_key,
            'v': api_version,
            'region': f"{county_name}, Ohio" if county_name else "Ohio",
            'parcel_id': parcel_id,
            'return_buildings': 'true',
            'rpp': 10
        }
        
        response = requests.get(base_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK' and data.get('results'):
                return {
                    "status": "OK",
                    "results": data.get('results', []),
                    "api_source": "AI PropIQ - Ohio Statewide",
                    "total_records": data.get('count', 0),
                    "query_info": data.get('query', ''),
                    "raw_response": data  # Include raw JSON response
                }
            else:
                return {
                    "status": "NOT_FOUND",
                    "message": f"No property found with parcel ID '{parcel_id}' in Ohio.",
                    "raw_response": data
                }
        elif response.status_code == 401:
            return {
                "status": "ERROR", 
                "message": "API authentication failed. Please check your API client key.",
                "raw_response": None
            }
        elif response.status_code == 429:
            return {
                "status": "ERROR", 
                "message": "API rate limit exceeded. Please try again later.",
                "raw_response": None
            }
        else:
            return {
                "status": "ERROR", 
                "message": f"API returned status code: {response.status_code}. Response: {response.text[:200]}",
                "raw_response": None
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "ERROR", 
            "message": "Request timed out. The API may be experiencing delays.",
            "raw_response": None
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "ERROR", 
            "message": "Connection error. Unable to reach API.",
            "raw_response": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "ERROR", 
            "message": f"Request error: {str(e)}",
            "raw_response": None
        }
    except Exception as e:
        return {
            "status": "ERROR", 
            "message": f"Unexpected error: {str(e)}",
            "raw_response": None
        }

def search_multiple_parcels_ohio(parcel_ids, county_name=None):
    """
    Search multiple parcel IDs at once using ReportAllUSA API
    """
    try:
        client_key = PROPERTY_API_CONFIG["REPORTALLUSA_CLIENT_KEY"]
        if not client_key:
            return {
                "status": "ERROR", 
                "message": "API client key not configured.",
                "raw_response": None
            }

        base_url = PROPERTY_API_CONFIG["REPORTALLUSA_BASE_URL"]
        api_version = PROPERTY_API_CONFIG["API_VERSION"]
        
        # Join multiple parcel IDs with semicolon as per API documentation
        parcel_ids_str = ";".join(parcel_ids) if isinstance(parcel_ids, list) else parcel_ids
        
        params = {
            'client': client_key,
            'v': api_version,
            'region': f"{county_name}, Ohio" if county_name else "Ohio",
            'parcel_id': parcel_ids_str,
            'return_buildings': 'true',
            'rpp': 50  # Higher limit for multiple parcels
        }
        
        response = requests.get(base_url, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return {
                    "status": "OK",
                    "results": data.get('results', []),
                    "api_source": "AI PropIQ - Ohio Statewide",
                    "total_records": data.get('count', 0),
                    "query_info": data.get('query', ''),
                    "raw_response": data  # Include raw JSON response
                }
            else:
                return {
                    "status": "NOT_FOUND",
                    "message": "No properties found for the provided parcel IDs in Ohio.",
                    "raw_response": data
                }
        else:
            return {
                "status": "ERROR", 
                "message": f"API error: {response.status_code}",
                "raw_response": None
            }
            
    except Exception as e:
        return {
            "status": "ERROR", 
            "message": f"Multiple parcel search error: {str(e)}",
            "raw_response": None
        }

def search_ohio_property_comprehensive(search_term, search_type="parcel", county_name=None):
    """
    Comprehensive Ohio property search using ReportAllUSA API with state-wide coverage
    """
    if search_type == "parcel":
        # Handle single or multiple parcel IDs
        if ";" in search_term or "," in search_term:
            # Multiple parcel IDs
            parcel_ids = [pid.strip() for pid in search_term.replace(",", ";").split(";")]
            return search_multiple_parcels_ohio(parcel_ids, county_name)
        else:
            # Single parcel ID
            return fetch_ohio_property_data_reportallusa(search_term, county_name)
    else:
        # For address searches, we'll still use parcel search but inform user
        return {
            "status": "ERROR",
            "message": "Address search not directly supported. Please use parcel ID search for Ohio properties.",
            "raw_response": None
        }

# --------------------------
# Clean Property Display Functions (No HTML, Clean Info Only)
# --------------------------
def create_clean_property_info_cards(data):
    """Create clean property information cards without HTML formatting"""
    
    # Highlighted Address Section
    property_address = data.get('address', data.get('property_address', data.get('street_address', 'N/A')))
    city = data.get('addr_city', data.get('city', data.get('municipality', 'N/A')))
    zip_code = data.get('addr_zip', data.get('zip', data.get('zip_code', data.get('postal_code', 'N/A'))))
    zip_plus_four = data.get('addr_zipplusfour', '')
    full_zip = f"{zip_code}-{zip_plus_four}" if zip_plus_four else zip_code
    
    st.markdown(f"""
    <div class='address-highlight'>
        <h3>📍 Property Address</h3>
        <div class='address-text'>{property_address}</div>
        <div class='address-text'>{city}, OH {full_zip}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mailing Address Section
    mail_address1 = data.get('mail_address1', 'N/A')
    mail_address3 = data.get('mail_address3', 'N/A')
    
    if mail_address1 != 'N/A' or mail_address3 != 'N/A':
        st.markdown(f"""
        <div class='mailing-address'>
            <h4>📮 Mailing Address</h4>
            <div>{mail_address1}</div>
            <div>{mail_address3}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main property overview with gradient cards (Light Blue Theme)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Market Value - Light Blue gradient
        market_value = data.get('mkt_val_tot', data.get('market_value', data.get('assessed_value', data.get('appraised_value', 0))))
        try:
            market_value = float(market_value) if market_value else 0
        except:
            market_value = 0
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(66,165,245,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>💰 Market Value</h4>
            <div style='font-size: 24px; font-weight: bold; margin-bottom: 10px;'>${market_value:,.0f}</div>
            <div style='font-size: 12px; opacity: 0.9;'>Total Market Value</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Parcel Information - Medium Blue gradient
        parcel_id = data.get('parcel_id', data.get('parcelid', data.get('parcel_number', 'N/A')))
        county_name = data.get('county_name', data.get('county', 'N/A'))
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(33,150,243,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>📋 Parcel Info</h4>
            <div style='margin-bottom: 12px;'><strong>Parcel ID:</strong><br><span style='font-size: 14px; font-weight: bold;'>{parcel_id}</span></div>
            <div><strong>County:</strong><br><span style='font-size: 14px;'>{county_name}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Property Details - Light Blue gradient
        land_use_class = data.get('land_use_class', data.get('property_type', data.get('land_use', data.get('property_class', 'N/A'))))
        bldg_sqft = data.get('bldg_sqft', data.get('square_feet', data.get('sqft', 'N/A')))
        acreage = data.get('acreage', data.get('lot_size', data.get('lot_area', 'N/A')))
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #64B5F6 0%, #42A5F5 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(100,181,246,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>🏘️ Property Info</h4>
            <div style='margin-bottom: 12px;'><strong>Type:</strong><br><span style='font-size: 14px; font-weight: bold;'>{land_use_class}</span></div>
            <div style='margin-bottom: 12px;'><strong>Building Sq Ft:</strong><br><span style='font-size: 14px;'>{bldg_sqft}</span></div>
            <div><strong>Acreage:</strong><br><span style='font-size: 14px;'>{acreage}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Owner Information - Dark Blue gradient
        owner = data.get('owner', data.get('owner_name', data.get('property_owner', 'N/A')))
        school_district = data.get('school_district', data.get('district', 'N/A'))
        owner_occupied = data.get('owner_occupied', 'N/A')
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(25,118,210,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>👤 Owner Info</h4>
            <div style='margin-bottom: 12px;'><strong>Owner:</strong><br><span style='font-size: 12px; font-weight: bold;'>{owner}</span></div>
            <div style='margin-bottom: 12px;'><strong>Owner Occupied:</strong><br><span style='font-size: 14px;'>{owner_occupied}</span></div>
            <div><strong>School District:</strong><br><span style='font-size: 11px;'>{school_district}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

# --------------------------
# Clean JSON Information Display on Main Page
# --------------------------
def display_clean_property_details(data):
    """Display comprehensive property data in clean format on main page"""
    
    st.subheader("📊 Complete Property Information")
    
    # Create tabs for organized information display
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏛️ Basic Info", "📍 Address Details", "👤 Owner Info", 
        "💰 Financial Data", "🏠 Property Details", "🗺️ Location Data"
    ])
    
    with tab1:
        st.write("**Basic Property Information**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Parcel ID:** {data.get('parcel_id', 'N/A')}")
            st.write(f"**County ID:** {data.get('county_id', 'N/A')}")
            st.write(f"**County Name:** {data.get('county_name', 'N/A')}")
            st.write(f"**Municipality:** {data.get('muni_name', 'N/A')}")
        with col2:
            st.write(f"**Census Place:** {data.get('census_place', 'N/A')}")
            st.write(f"**State:** {data.get('state_abbr', 'N/A')}")
            st.write(f"**Robust ID:** {data.get('robust_id', 'N/A')}")
            st.write(f"**Last Updated:** {data.get('last_updated', 'N/A')}")
    
    with tab2:
        st.write("**Address Information**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Full Address:** {data.get('address', 'N/A')}")
            st.write(f"**Address Number:** {data.get('addr_number', 'N/A')}")
            st.write(f"**Street Name:** {data.get('addr_street_name', 'N/A')}")
            st.write(f"**Street Type:** {data.get('addr_street_type', 'N/A')}")
        with col2:
            st.write(f"**City:** {data.get('addr_city', 'N/A')}")
            st.write(f"**ZIP Code:** {data.get('addr_zip', 'N/A')}")
            st.write(f"**ZIP+4:** {data.get('addr_zipplusfour', 'N/A')}")
            st.write(f"**Census ZIP:** {data.get('census_zip', 'N/A')}")
        
        st.write("**Mailing Address**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Mail Address Line 1:** {data.get('mail_address1', 'N/A')}")
            st.write(f"**Mail Address Line 3:** {data.get('mail_address3', 'N/A')}")
            st.write(f"**Mail Street Name:** {data.get('mail_streetname', 'N/A')}")
            st.write(f"**Mail Street Type:** {data.get('mail_streetnameposttype', 'N/A')}")
        with col2:
            st.write(f"**Mail Place Name:** {data.get('mail_placename', 'N/A')}")
            st.write(f"**Mail State:** {data.get('mail_statename', 'N/A')}")
            st.write(f"**Mail ZIP Code:** {data.get('mail_zipcode', 'N/A')}")
    
    with tab3:
        st.write("**Owner Information**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Owner Name:** {data.get('owner', 'N/A')}")
            st.write(f"**Owner Occupied:** {data.get('owner_occupied', 'N/A')}")
        with col2:
            st.write(f"**School District:** {data.get('school_district', 'N/A')}")
            st.write(f"**Municipality ID:** {data.get('muni_id', 'N/A')}")
    
    with tab4:
        st.write("**Financial Information**")
        col1, col2 = st.columns(2)
        with col1:
            try:
                sale_price = f"${float(data.get('sale_price', 0)):,.2f}" if data.get('sale_price') else 'N/A'
                mkt_val_land = f"${float(data.get('mkt_val_land', 0)):,.2f}" if data.get('mkt_val_land') else 'N/A'
                mkt_val_bldg = f"${float(data.get('mkt_val_bldg', 0)):,.2f}" if data.get('mkt_val_bldg') else 'N/A'
                mkt_val_tot = f"${float(data.get('mkt_val_tot', 0)):,.2f}" if data.get('mkt_val_tot') else 'N/A'
            except:
                sale_price = mkt_val_land = mkt_val_bldg = mkt_val_tot = 'N/A'
            
            st.write(f"**Sale Price:** {sale_price}")
            st.write(f"**Market Value - Land:** {mkt_val_land}")
        with col2:
            st.write(f"**Market Value - Building:** {mkt_val_bldg}")
            st.write(f"**Market Value - Total:** {mkt_val_tot}")
            st.write(f"**Transaction Date:** {data.get('trans_date', 'N/A')}")
    
    with tab5:
        st.write("**Property Characteristics**")
        col1, col2 = st.columns(2)
        with col1:
            bldg_sqft = f"{int(data.get('bldg_sqft', 0)):,} sq ft" if data.get('bldg_sqft') and str(data.get('bldg_sqft')).isdigit() else data.get('bldg_sqft', 'N/A')
            acreage = f"{float(data.get('acreage', 0)):.3f} acres" if data.get('acreage') else 'N/A'
            
            st.write(f"**Building Sq Ft:** {bldg_sqft}")
            st.write(f"**Land Use Code:** {data.get('land_use_code', 'N/A')}")
            st.write(f"**Land Use Class:** {data.get('land_use_class', 'N/A')}")
            st.write(f"**Acreage:** {acreage}")
        with col2:
            st.write(f"**Calculated Acreage:** {data.get('acreage_calc', 'N/A')}")
            st.write(f"**Number of Buildings:** {data.get('buildings', 'N/A')}")
            st.write(f"**Zoning:** {data.get('zoning', 'N/A')}")
            st.write(f"**USPS Classification:** {data.get('usps_residential', 'N/A')}")
    
    with tab6:
        st.write("**Location Information**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Latitude:** {data.get('latitude', 'N/A')}")
            st.write(f"**Longitude:** {data.get('longitude', 'N/A')}")
            st.write(f"**Elevation:** {data.get('elevation', 'N/A')}")
            st.write(f"**Neighborhood Code:** {data.get('ngh_code', 'N/A')}")
        with col2:
            st.write(f"**Census Block:** {data.get('census_block', 'N/A')}")
            st.write(f"**Census Tract:** {data.get('census_tract', 'N/A')}")
        
        # Land Cover and Crop Cover Information
        if 'land_cover' in data and data['land_cover']:
            st.write("**Land Cover:**")
            for cover_type, percentage in data['land_cover'].items():
                st.write(f"  • {cover_type}: {percentage}")
        
        if 'crop_cover' in data and data['crop_cover']:
            st.write("**Crop Cover:**")
            for crop_type, percentage in data['crop_cover'].items():
                st.write(f"  • {crop_type}: {percentage}")

# --------------------------
# Combined PDF Generation for All Searches
# --------------------------
def create_combined_pdf_report():
    """Create a combined PDF report for all searches in the session"""
    if not st.session_state.all_search_results:
        return None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("Ohio Property Tax Combined Report - AI PropIQ", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph(f"Session ID: {st.session_state.app_session_id}", styles['Normal']))
    story.append(Paragraph(f"Total Searches: {len(st.session_state.all_search_results)}", styles['Normal']))
    story.append(Spacer(1, 30))

    # Add each search result
    for i, search_entry in enumerate(st.session_state.all_search_results):
        # Search header
        search_header_style = ParagraphStyle(
            'SearchHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.darkblue
        )
        story.append(Paragraph(f"Search #{search_entry['search_id']}: Parcel ID {search_entry['parcel_id']}", search_header_style))
        story.append(Paragraph(f"Search Time: {search_entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"County Filter: {search_entry['county_filter']}", styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Property data for each result
        for j, property_data in enumerate(search_entry['results']):
            if j > 0:  # Add space between multiple properties in same search
                story.append(Spacer(1, 15))
            
            # Property overview table
            overview_data = [
                ['Property Information', 'Details'],
                ['Parcel ID', property_data.get('parcel_id', 'N/A')],
                ['Property Address', property_data.get('address', 'N/A')],
                ['City, State ZIP', f"{property_data.get('addr_city', 'N/A')}, OH {property_data.get('addr_zip', 'N/A')}"],
                ['County', property_data.get('county_name', 'N/A')],
                ['Owner', property_data.get('owner', 'N/A')],
                ['Market Value Total', f"${float(property_data.get('mkt_val_tot', 0)):,.2f}"],
                ['Market Value Land', f"${float(property_data.get('mkt_val_land', 0)):,.2f}"],
                ['Market Value Building', f"${float(property_data.get('mkt_val_bldg', 0)):,.2f}"],
                ['Land Use Class', property_data.get('land_use_class', 'N/A')],
                ['Building Sq Ft', property_data.get('bldg_sqft', 'N/A')],
                ['Acreage', property_data.get('acreage', 'N/A')],
                ['School District', property_data.get('school_district', 'N/A')]
            ]
            
            table = Table(overview_data, colWidths=[2.5*inch, 3.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.lightblue),
                ('GRID',(0,0),(-1,-1),1,colors.black),
                ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('FONTSIZE',(0,0),(-1,-1),9)
            ]))
            story.append(table)
        
        story.append(Spacer(1, 20))
        
        # Add page break between searches (except for last one)
        if i < len(st.session_state.all_search_results) - 1:
            story.append(Spacer(1, 50))

    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("Report generated by AI PropIQ - Ohio Property Tax Lookup Pro", styles['Normal']))
    story.append(Paragraph("Data coverage: Ohio Statewide Property Information", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------
# Enhanced PDF Generation for Single Property
# --------------------------
def create_enhanced_ohio_pdf(data):
    """Create enhanced PDF report for Ohio property data"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("Ohio Property Tax Report - AI PropIQ", title_style))
    story.append(Spacer(1, 20))

    # Property overview table with enhanced data
    overview_data = [
        ['Property Information', 'Details'],
        ['Parcel ID', data.get('parcel_id', data.get('parcelid', 'N/A'))],
        ['Property Address', data.get('address', data.get('property_address', 'N/A'))],
        ['City, State ZIP', f"{data.get('addr_city', data.get('city', 'N/A'))}, OH {data.get('addr_zip', data.get('zip', 'N/A'))}"],
        ['County', data.get('county_name', data.get('county', 'N/A'))],
        ['Owner', data.get('owner', data.get('owner_name', 'N/A'))],
        ['Market Value Total', f"${float(data.get('mkt_val_tot', data.get('market_value', 0))):,.2f}"],
        ['Market Value Land', f"${float(data.get('mkt_val_land', 0)):,.2f}"],
        ['Market Value Building', f"${float(data.get('mkt_val_bldg', 0)):,.2f}"],
        ['Land Use Class', data.get('land_use_class', data.get('property_type', 'N/A'))],
        ['Building Sq Ft', data.get('bldg_sqft', 'N/A')],
        ['Acreage', data.get('acreage', 'N/A')],
        ['School District', data.get('school_district', 'N/A')]
    ]
    
    table = Table(overview_data, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightblue),
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('FONTSIZE',(0,0),(-1,-1),10)
    ]))
    story.append(table)
    story.append(Spacer(1,20))

    # Add data source information
    story.append(Paragraph("Data Source Information", styles['Heading2']))
    story.append(Paragraph(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph("Data provided by: AI PropIQ API", styles['Normal']))
    story.append(Paragraph("Coverage: Ohio Statewide Property Data", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------
# Initialize Session State
# --------------------------
initialize_session_state()

# Maximum usage limit
MAX_SEARCHES = 10

# --------------------------
# Sidebar: Enhanced Ohio counties display and usage stats
# --------------------------
with st.sidebar:
    st.header("📈 Usage Statistics")
    usage_remaining = MAX_SEARCHES - st.session_state.usage_count
    if usage_remaining > 0:
        st.metric("Searches Remaining", usage_remaining)
        progress_value = st.session_state.usage_count / MAX_SEARCHES
        st.progress(progress_value)
        
        # Color-coded warning
        if usage_remaining <= 2:
            st.error(f"⚠️ Only {usage_remaining} searches left!")
        elif usage_remaining <= 5:
            st.warning(f"⚠️ {usage_remaining} searches remaining")
        else:
            st.success(f"✅ {usage_remaining} searches available")
    else:
        st.error("❌ Usage limit reached (10 searches)")
        st.markdown("**Refresh the page to reset your search count**")
    
    # Premium subscription link
    st.markdown("""
    <div class='premium-link'>
        <h4 style='color: white; margin-bottom: 10px;'>🚀 Get Premium Access</h4>
        <a href='https://aipropiq.com/product/monthsubscription/' target='_blank'>
            Upgrade to Premium for Unlimited Searches
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Session information
    st.subheader("📊 Session Info")
    st.write(f"**Session ID:** {st.session_state.app_session_id}")
    st.write(f"**Total Searches:** {len(st.session_state.all_search_results)}")
    if st.session_state.last_search_timestamp:
        st.write(f"**Last Search:** {st.session_state.last_search_timestamp.strftime('%H:%M:%S')}")
    
    # Combined PDF download
    if st.session_state.all_search_results:
        st.divider()
        st.subheader("📄 Combined Report")
        combined_pdf = create_combined_pdf_report()
        if combined_pdf:
            st.download_button(
                "📄 Download Combined PDF Report",
                combined_pdf.getvalue(),
                file_name=f"ohio_combined_report_{st.session_state.app_session_id}.pdf",
                mime="application/pdf",
                help="Download a combined PDF report of all searches in this session"
            )
    
    st.divider()
    
    # Recent searches
    if st.session_state.search_history:
        st.subheader("🕒 Recent Searches")
        for search in st.session_state.search_history[-5:]:  # Show last 5 searches
            st.text(search)
    
    st.divider()
    
    # Reset usage button
    if st.button("🔄 Reset Usage Count", help="Reset your search count to start over"):
        st.session_state.usage_count = 0
        st.session_state.search_history = []
        st.session_state.cached_results = {}
        st.session_state.all_search_results = []
        st.session_state.current_property_data = None
        st.session_state.last_search_timestamp = None
        st.rerun()

# --------------------------
# Main App UI - Enhanced
# --------------------------
st.title("🏠 Ohio Property Tax Lookup Pro - AI PropIQ")
st.markdown("**Comprehensive Ohio property research with real data integration** | *10 searches per session*")

# Enhanced region information
st.info("🌟 **Now covering ALL 88 Ohio counties** with real property data from AI PropIQ API for complete statewide coverage.")

# Premium subscription banner
st.markdown("""
<div class='premium-link'>
    <h4 style='color: white; margin-bottom: 10px;'>🚀 Need More Searches?</h4>
    <a href='https://aipropiq.com/product/monthsubscription/' target='_blank'>
        Get Premium Access for Unlimited Property Searches
    </a>
</div>
""", unsafe_allow_html=True)

# Check usage limit
if st.session_state.usage_count >= MAX_SEARCHES:
    st.error("❌ Maximum usage reached (10 searches). Please refresh the page to reset.")
    st.info("💡 **Tip:** Refresh the page or use the reset button in the sidebar to start over.")
    st.markdown("""
    <div class='premium-link'>
        <h4 style='color: white; margin-bottom: 10px;'>🚀 Want Unlimited Access?</h4>
        <a href='https://aipropiq.com/product/monthsubscription/' target='_blank'>
            Upgrade to Premium - No Search Limits!
        </a>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Main search interface (removed tabs, keeping only parcel search)
st.subheader("🔍 Ohio State-wide Property Search by Parcel ID")
st.markdown("*Search any property across all of Ohio using parcel ID - no county selection needed!*")

col1, col2, col3 = st.columns([4, 2, 1])
with col1:
    parcel_id = st.text_input(
        "Enter Ohio Parcel ID", 
        placeholder="e.g., 44327012 or multiple: 44327012;44327010;44327013", 
        help="Enter single parcel ID or multiple IDs separated by semicolons. Searches entire state of Ohio automatically."
    )
with col2:
    county_filter = st.selectbox(
        "County Filter (Optional)",
        ["All of Ohio (Recommended)"] + [f"{info['name']}" for info in OHIO_COUNTIES.values()],
        help="Leave as 'All of Ohio' for best results, or select specific county to narrow search"
    )
with col3:
    search_button = st.button(
        "🔍 Search Ohio", 
        type="primary", 
        disabled=(st.session_state.usage_count >= MAX_SEARCHES)
    )

# Enhanced parcel ID search functionality
if search_button and parcel_id:
    if st.session_state.usage_count >= MAX_SEARCHES:
        st.error("Usage limit reached!")
    elif not parcel_id.strip():
        st.error("Please enter a valid Parcel ID")
    else:
        with st.spinner("Searching Ohio state-wide property database..."):
            try:
                # Determine county name if selected
                county_name = None
                if county_filter != "All of Ohio (Recommended)":
                    county_name = county_filter
                
                # Use comprehensive search function
                api_response = search_ohio_property_comprehensive(parcel_id, "parcel", county_name)

                if api_response.get('status') == "OK" and api_response.get('results'):
                    # Update usage count and history
                    st.session_state.usage_count += 1
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    search_scope = f" - {county_filter}" if county_filter != "All of Ohio (Recommended)" else " - Statewide"
                    st.session_state.search_history.append(f"{parcel_id}{search_scope} - {timestamp}")
                    
                    # Add to session search results
                    add_search_to_history(parcel_id, county_filter, api_response['results'])
                    
                    # Success message
                    total_found = api_response.get('total_records', len(api_response.get('results', [])))
                    st.success(f"✅ Found {total_found} Ohio property record(s)! (Search {st.session_state.usage_count}/{MAX_SEARCHES}) - Source: {api_response.get('api_source', 'AI PropIQ')}")
                    
                    # Display results
                    results = api_response['results']
                    if len(results) == 1:
                        create_clean_property_info_cards(results[0])
                        # Display comprehensive property details on main page
                        display_clean_property_details(results[0])
                    else:
                        st.info(f"Found {len(results)} matching properties:")
                        for i, property_data in enumerate(results[:5]):  # Show top 5 results
                            county_name = property_data.get('county_name', property_data.get('county', 'N/A'))
                            address = property_data.get('address', property_data.get('property_address', 'N/A'))
                            with st.expander(f"Property {i+1}: {address} - {county_name}"):
                                create_clean_property_info_cards(property_data)
                                display_clean_property_details(property_data)

                    # Enhanced export options with JSON Raw Response
                    st.divider()
                    st.subheader("📥 Export Options")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        pdf_buffer = create_enhanced_ohio_pdf(results[0])
                        st.download_button(
                            "📄 Download PDF Report", 
                            pdf_buffer.getvalue(),
                            file_name=f"ohio_property_report_{parcel_id.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                            mime="application/pdf"
                        )
                    with col2:
                        json_str = json.dumps(results[0] if len(results) == 1 else results, indent=2)
                        st.download_button(
                            "📋 Download Property JSON", 
                            json_str,
                            file_name=f"ohio_property_data_{parcel_id.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                            mime="application/json"
                        )
                    with col3:
                        # Raw API Response JSON
                        if api_response.get('raw_response'):
                            raw_json_str = json.dumps(api_response['raw_response'], indent=2)
                            st.download_button(
                                "🔧 Download Raw API Response", 
                                raw_json_str,
                                file_name=f"raw_api_response_{parcel_id.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                                mime="application/json"
                            )
                    
                    # Display Raw JSON Response
                    if api_response.get('raw_response'):
                        st.divider()
                        st.subheader("🔧 Raw API Response")
                        with st.expander("View Raw JSON Response from AI PropIQ API", expanded=False):
                            st.json(api_response['raw_response'])
                            
                else:
                    error_msg = api_response.get('message', 'Property not found in Ohio records')
                    st.error(f"❌ {error_msg}")
                    st.info("💡 Please verify the Parcel ID format and try again. You can search multiple parcel IDs by separating them with semicolons (;).")
                    
                    # Show raw response even for errors if available
                    if api_response.get('raw_response'):
                        with st.expander("View Raw API Response", expanded=False):
                            st.json(api_response['raw_response'])
                    
                    # Still increment usage count for failed searches
                    st.session_state.usage_count += 1
                    
            except Exception as e:
                st.error(f"❌ Unexpected error occurred: {str(e)}")
                st.info("💡 Please try again or contact support")
                # Increment usage count for errors too
                st.session_state.usage_count += 1

# Footer with premium link
st.divider()
st.markdown("""
<div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin: 20px 0;'>
    <h4>🚀 Ready for More?</h4>
    <p>Get unlimited property searches, advanced features, and priority support with our Premium subscription.</p>
    <div class='premium-link'>
        <a href='https://aipropiq.com/product/monthsubscription/' target='_blank'>
            Start Your Premium Subscription Today
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

# Custom footer
st.markdown("""
<div class='custom-footer'>
    <p>Ohio Property Tax Lookup Pro - Powered by AI PropIQ | 
    <a href='https://aipropiq.com/product/monthsubscription/' target='_blank' style='color: #2196F3;'>Get Premium Access</a></p>
</div>
""", unsafe_allow_html=True)
