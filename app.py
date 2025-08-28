import streamlit as st
from utils.auth import initialize_auth_state, show_auth_page
from utils.database import get_user_usage

st.set_page_config(
    page_title="RentCast Property Analytics",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication state
initialize_auth_state()

# Main page content
st.title("🏡 RentCast Property Analytics")
st.markdown("---")

if st.session_state.user is None:
    show_auth_page()
else:
    user_email = st.session_state.user.email
    user_id = st.session_state.user.id
    
    # Welcome message and quick stats
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.success(f"Welcome back, {user_email}!")
    
    with col2:
        try:
            queries_used = get_user_usage(user_id, user_email)
        except Exception as e:
            st.error(f"Error fetching usage: {e}")
            queries_used = 0
        st.metric("Queries Used", f"{queries_used}/30")
    
    with col3:
        remaining = max(30 - queries_used, 0)
        st.metric("Remaining", remaining)
    
    st.markdown("---")
    
    # App overview
    st.subheader("📋 Available Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🏠 Property Search
        - Search properties by address
        - Get detailed property information
        - View market analytics
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Usage Dashboard
        - Track your API usage
        - View query history
        - Monitor account limits
        """)
    
    with col3:
        st.markdown("""
        ### 👤 Profile Management
        - Update account settings
        - Change password
        - Manage preferences
        """)
    
    st.markdown("---")
    st.info("💡 Use the sidebar navigation to access different features of the application.")
