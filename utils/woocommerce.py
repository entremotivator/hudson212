import requests
import streamlit as st
from datetime import datetime
import hashlib
import hmac
import base64
from urllib.parse import urlencode

class WooCommerceAPI:
    def __init__(self):
        """Initialize WooCommerce API client."""
        self.base_url = st.secrets["wordpress"]["base_url"].rstrip('/')
        self.consumer_key = st.secrets["woocommerce"]["consumer_key"]
        self.consumer_secret = st.secrets["woocommerce"]["consumer_secret"]
        self.api_url = f"{self.base_url}/wp-json/wc/v3"
    
    def _get_auth_headers(self):
        """Get authentication headers for WooCommerce API."""
        auth_string = f"{self.consumer_key}:{self.consumer_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        return {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json'
        }
    
    def get_orders(self, customer_email=None, status='completed', per_page=100):
        """Get orders from WooCommerce."""
        try:
            params = {
                'status': status,
                'per_page': per_page
            }
            if customer_email:
                params['customer'] = customer_email
            
            response = requests.get(
                f"{self.api_url}/orders",
                headers=self._get_auth_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching orders: {e}")
            return []
    
    def get_order_by_id(self, order_id):
        """Get specific order by ID."""
        try:
            response = requests.get(
                f"{self.api_url}/orders/{order_id}",
                headers=self._get_auth_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching order {order_id}: {e}")
            return None
    
    def verify_product_purchase(self, customer_email, product_id="i90"):
        """Verify if customer has purchased the specific product."""
        try:
            orders = self.get_orders(customer_email=customer_email, status='completed')
            
            for order in orders:
                # Check line items for the specific product
                for item in order.get('line_items', []):
                    # Check if product ID matches or if SKU matches
                    if (str(item.get('product_id')) == str(product_id) or 
                        item.get('sku') == product_id or
                        str(item.get('variation_id')) == str(product_id)):
                        return {
                            'verified': True,
                            'order_id': order['id'],
                            'order_date': order['date_created'],
                            'customer_data': {
                                'email': order['billing']['email'],
                                'first_name': order['billing']['first_name'],
                                'last_name': order['billing']['last_name'],
                                'phone': order['billing'].get('phone', ''),
                                'company': order['billing'].get('company', '')
                            }
                        }
            
            return {'verified': False, 'message': 'No completed purchase found for this product'}
            
        except Exception as e:
            st.error(f"Error verifying purchase: {e}")
            return {'verified': False, 'error': str(e)}
    
    def get_customer_by_email(self, email):
        """Get customer data by email."""
        try:
            response = requests.get(
                f"{self.api_url}/customers",
                headers=self._get_auth_headers(),
                params={'email': email}
            )
            response.raise_for_status()
            customers = response.json()
            return customers[0] if customers else None
        except Exception as e:
            st.error(f"Error fetching customer: {e}")
            return None

def check_woocommerce_access(email):
    """Check if user has access based on WooCommerce purchase."""
    wc = WooCommerceAPI()
    result = wc.verify_product_purchase(email, "i90")
    return result

def get_customer_data_from_woocommerce(email):
    """Get customer data from WooCommerce for user creation."""
    wc = WooCommerceAPI()
    verification = wc.verify_product_purchase(email, "i90")
    
    if verification.get('verified'):
        return verification.get('customer_data')
    return None

