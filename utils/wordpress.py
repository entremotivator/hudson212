import requests
import streamlit as st
from datetime import datetime
import base64

class WordPressAPI:
    def __init__(self):
        """Initialize WordPress API client."""
        self.base_url = st.secrets["wordpress"]["base_url"].rstrip('/')
        self.username = st.secrets["wordpress"]["username"]
        self.password = st.secrets["wordpress"]["password"]
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
    
    def _get_auth_headers(self):
        """Get authentication headers for WordPress API."""
        auth_string = f"{self.username}:{self.password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        return {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json'
        }
    
    def get_user_by_email(self, email):
        """Get WordPress user by email."""
        try:
            response = requests.get(
                f"{self.api_url}/users",
                headers=self._get_auth_headers(),
                params={'search': email}
            )
            response.raise_for_status()
            users = response.json()
            
            # Find exact email match
            for user in users:
                if user.get('email', '').lower() == email.lower():
                    return user
            return None
            
        except Exception as e:
            st.error(f"Error fetching WordPress user: {e}")
            return None
    
    def create_wordpress_user(self, email, first_name, last_name, password=None):
        """Create a new WordPress user."""
        try:
            # Generate a random password if not provided
            if not password:
                import secrets
                import string
                password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            
            user_data = {
                'username': email.split('@')[0],  # Use email prefix as username
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'password': password,
                'roles': ['subscriber']  # Default role
            }
            
            response = requests.post(
                f"{self.api_url}/users",
                headers=self._get_auth_headers(),
                json=user_data
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            st.error(f"Error creating WordPress user: {e}")
            return None
    
    def sync_user_data(self, email):
        """Sync user data from WordPress."""
        try:
            wp_user = self.get_user_by_email(email)
            if wp_user:
                return {
                    'id': wp_user['id'],
                    'email': wp_user['email'],
                    'first_name': wp_user.get('first_name', ''),
                    'last_name': wp_user.get('last_name', ''),
                    'display_name': wp_user.get('name', ''),
                    'roles': wp_user.get('roles', []),
                    'registered_date': wp_user.get('registered_date', ''),
                    'meta': wp_user.get('meta', {})
                }
            return None
            
        except Exception as e:
            st.error(f"Error syncing WordPress user data: {e}")
            return None

def sync_wordpress_user_data(email):
    """Sync user data from WordPress."""
    wp = WordPressAPI()
    return wp.sync_user_data(email)

def create_wordpress_user_if_not_exists(email, first_name, last_name):
    """Create WordPress user if they don't exist."""
    wp = WordPressAPI()
    existing_user = wp.get_user_by_email(email)
    
    if not existing_user:
        return wp.create_wordpress_user(email, first_name, last_name)
    return existing_user

