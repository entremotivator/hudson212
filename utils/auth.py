import streamlit as st
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_ANON_KEY = st.secrets["supabase"]["anon_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def initialize_auth_state():
    """Initialize authentication-related session state variables."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None

def get_user_client():
    """Return Supabase client authorized with current user's access token."""
    if "access_token" not in st.session_state:
        return None
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(st.session_state.access_token)
    return client

def login(email, password):
    """Handle user login with automatic provisioning if needed."""
    try:
        # First try to login normally
        user = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if user and user.session:
            st.session_state.access_token = user.session.access_token
            st.session_state.user = user.user
            return user
        
    except Exception as login_error:
        # If login fails, check if user has WooCommerce access and needs provisioning
        try:
            # Dynamic import to avoid circular dependency
            from utils.user_provisioning import verify_and_provision_user, check_user_access_status
            
            access_status = check_user_access_status(email)
            
            if access_status.get('has_access'):
                st.info("🔄 Verifying your purchase and setting up your account...")
                
                # Try to provision the user
                provision_result = verify_and_provision_user(email)
                
                if provision_result.get('success'):
                    if not provision_result.get('exists'):
                        # New user was created, show them their temporary password
                        temp_password = provision_result.get('password')
                        st.success(f"✅ Account created! Your temporary password is: **{temp_password}**")
                        st.warning("⚠️ Please save this password and consider changing it after login.")
                        
                        # Try to login with the new credentials
                        try:
                            user = supabase.auth.sign_in_with_password({
                                "email": email,
                                "password": temp_password
                            })
                            if user and user.session:
                                st.session_state.access_token = user.session.access_token
                                st.session_state.user = user.user
                                return user
                        except:
                            st.error("Account created but auto-login failed. Please use the temporary password above.")
                    else:
                        st.error("Account exists but password is incorrect. Please contact support.")
                else:
                    st.error(f"Failed to create account: {provision_result.get('message')}")
            else:
                st.error("Login failed: Invalid credentials or no valid purchase found.")
                
        except Exception as provision_error:
            st.error(f"Login failed: {str(login_error)}")
            
        return None

def signup(email, password):
    """Handle user signup."""
    try:
        user = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if user and user.session:
            st.session_state.access_token = user.session.access_token
            st.session_state.user = user.user

            # Initialize usage tracking
            from utils.database import initialize_user_usage
            initialize_user_usage(str(user.user.id), email)
        return user
    except Exception as e:
        st.error(f"Signup failed: {e}")
        return None

def logout():
    """Handle user logout."""
    st.session_state.user = None
    st.session_state.access_token = None
    st.success("Logged out successfully!")
    st.rerun()

def show_auth_page():
    """Display authentication page with login only."""
    st.subheader("🔐 Please sign in to continue")
    
    st.info("💡 To get access, please purchase our service from our WooCommerce store and your account will be automatically created.")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
        
        if login_button and email and password:
            user = login(email, password)
            if user:
                st.success("Logged in successfully!")
                st.rerun()
    
    st.markdown("---")
    st.markdown("**Don't have an account?**")
    st.markdown("Purchase our service to get automatic access: [Visit Store](https://aipropiq.com/product/rental-analytics-access/)")
