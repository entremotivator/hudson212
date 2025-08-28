import streamlit as st
from supabase import create_client, Client
from utils.woocommerce import check_woocommerce_access, get_customer_data_from_woocommerce
from utils.wordpress import sync_wordpress_user_data, create_wordpress_user_if_not_exists
from utils.database import initialize_user_usage
import secrets
import string

# Supabase configuration
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_ANON_KEY = st.secrets["supabase"]["anon_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def generate_secure_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def create_supabase_user_from_woocommerce(email):
    """Create Supabase user based on WooCommerce purchase verification."""
    try:
        # First, verify the WooCommerce purchase
        wc_verification = check_woocommerce_access(email)
        
        if not wc_verification.get('verified'):
            return {
                'success': False,
                'message': 'No valid purchase found for this email'
            }
        
        # Get customer data from WooCommerce
        customer_data = get_customer_data_from_woocommerce(email)
        
        if not customer_data:
            return {
                'success': False,
                'message': 'Could not retrieve customer data from WooCommerce'
            }
        
        # Generate a secure password
        password = generate_secure_password()
        
        # Create user in Supabase
        user_response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # Auto-confirm email since they purchased
            "user_metadata": {
                "first_name": customer_data.get('first_name', ''),
                "last_name": customer_data.get('last_name', ''),
                "phone": customer_data.get('phone', ''),
                "company": customer_data.get('company', ''),
                "woocommerce_verified": True,
                "order_id": wc_verification.get('order_id'),
                "purchase_date": wc_verification.get('order_date')
            }
        })
        
        if user_response.user:
            user_id = user_response.user.id
            
            # Initialize usage tracking
            initialize_user_usage(str(user_id), email)
            
            # Sync with WordPress if needed
            try:
                wp_user = create_wordpress_user_if_not_exists(
                    email, 
                    customer_data.get('first_name', ''),
                    customer_data.get('last_name', '')
                )
            except Exception as wp_error:
                # WordPress sync failed but user was created in Supabase
                print(f"WordPress sync failed: {wp_error}")
            
            return {
                'success': True,
                'user_id': user_id,
                'email': email,
                'password': password,
                'message': 'User created successfully'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to create user in Supabase'
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Error creating user: {str(e)}'
        }

def verify_and_provision_user(email):
    """Main function to verify purchase and provision user if needed."""
    try:
        # Check if user already exists in Supabase
        existing_users = supabase.auth.admin.list_users()
        
        for user in existing_users:
            if user.email == email:
                return {
                    'success': True,
                    'exists': True,
                    'message': 'User already exists'
                }
        
        # User doesn't exist, verify purchase and create
        result = create_supabase_user_from_woocommerce(email)
        result['exists'] = False
        return result
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error in user provisioning: {str(e)}'
        }

def check_user_access_status(email):
    """Check if user has valid access based on WooCommerce purchase."""
    try:
        # Check WooCommerce purchase
        wc_verification = check_woocommerce_access(email)
        
        if wc_verification.get('verified'):
            return {
                'has_access': True,
                'source': 'woocommerce',
                'order_id': wc_verification.get('order_id'),
                'purchase_date': wc_verification.get('order_date')
            }
        
        return {
            'has_access': False,
            'message': 'No valid purchase found'
        }
        
    except Exception as e:
        return {
            'has_access': False,
            'error': str(e)
        }

