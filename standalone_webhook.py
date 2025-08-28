from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import requests
import base64
import secrets
import string

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration - these should be set as environment variables in production
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://nfqqhvflehwdxyxvlgja.supabase.co/')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', 'your-supabase-key')
WORDPRESS_BASE_URL = os.getenv('WORDPRESS_BASE_URL', 'https://aipropiq.com/')
WORDPRESS_USERNAME = os.getenv('WORDPRESS_USERNAME', 'your-username')
WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD', 'your-password')
WOOCOMMERCE_CONSUMER_KEY = os.getenv('WOOCOMMERCE_CONSUMER_KEY', 'your-woocommerce-consumer-key')
WOOCOMMERCE_CONSUMER_SECRET = os.getenv('WOOCOMMERCE_CONSUMER_SECRET', 'your-woocommerce-consumer-secret')

def generate_secure_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def get_woocommerce_auth_headers():
    """Get authentication headers for WooCommerce API."""
    auth_string = f"{WOOCOMMERCE_CONSUMER_KEY}:{WOOCOMMERCE_CONSUMER_SECRET}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    return {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/json'
    }

def verify_product_purchase(customer_email, product_id="i90"):
    """Verify if customer has purchased the specific product."""
    try:
        api_url = f"{WORDPRESS_BASE_URL.rstrip('/')}/wp-json/wc/v3"
        
        response = requests.get(
            f"{api_url}/orders",
            headers=get_woocommerce_auth_headers(),
            params={'status': 'completed', 'per_page': 100}
        )
        response.raise_for_status()
        orders = response.json()
        
        for order in orders:
            if order['billing']['email'].lower() == customer_email.lower():
                # Check line items for the specific product
                for item in order.get('line_items', []):
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
        return {'verified': False, 'error': str(e)}

def create_supabase_user(email, password, user_metadata):
    """Create user in Supabase."""
    try:
        headers = {
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
            'Content-Type': 'application/json',
            'apikey': SUPABASE_ANON_KEY
        }
        
        user_data = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": user_metadata
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            headers=headers,
            json=user_data
        )
        
        if response.status_code == 201:
            return {'success': True, 'user': response.json()}
        else:
            return {'success': False, 'error': response.text}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/webhook/woocommerce', methods=['POST'])
def woocommerce_webhook():
    """Handle WooCommerce webhook for order completion."""
    try:
        # Get the webhook data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Log the webhook for debugging
        print(f"Webhook received at {datetime.now()}: {json.dumps(data, indent=2)}")
        
        # Check if this is an order completion webhook
        if data.get('status') == 'completed':
            order_id = data.get('id')
            customer_email = data.get('billing', {}).get('email')
            
            if not customer_email:
                return jsonify({'error': 'No customer email found'}), 400
            
            # Check if the order contains our target product (item ID i90)
            line_items = data.get('line_items', [])
            has_target_product = False
            
            for item in line_items:
                if (str(item.get('product_id')) == 'i90' or 
                    item.get('sku') == 'i90' or
                    str(item.get('variation_id')) == 'i90'):
                    has_target_product = True
                    break
            
            if has_target_product:
                # Verify purchase and create user
                verification = verify_product_purchase(customer_email, "i90")
                
                if verification.get('verified'):
                    customer_data = verification.get('customer_data')
                    password = generate_secure_password()
                    
                    user_metadata = {
                        "first_name": customer_data.get('first_name', ''),
                        "last_name": customer_data.get('last_name', ''),
                        "phone": customer_data.get('phone', ''),
                        "company": customer_data.get('company', ''),
                        "woocommerce_verified": True,
                        "order_id": verification.get('order_id'),
                        "purchase_date": verification.get('order_date')
                    }
                    
                    result = create_supabase_user(customer_email, password, user_metadata)
                    
                    if result.get('success'):
                        return jsonify({
                            'status': 'success',
                            'message': 'User created successfully',
                            'email': customer_email,
                            'order_id': order_id,
                            'password': password  # In production, send this via email
                        })
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': f"Failed to create user: {result.get('error')}",
                            'email': customer_email,
                            'order_id': order_id
                        }), 500
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Purchase verification failed',
                        'email': customer_email,
                        'order_id': order_id
                    }), 400
            else:
                return jsonify({
                    'status': 'ignored',
                    'message': 'Order does not contain target product i90'
                })
        else:
            return jsonify({
                'status': 'ignored',
                'message': f'Order status is {data.get("status")}, not completed'
            })
            
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-access', methods=['POST'])
def check_access():
    """API endpoint to check user access status."""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        verification = verify_product_purchase(email, "i90")
        
        if verification.get('verified'):
            return jsonify({
                'has_access': True,
                'order_id': verification.get('order_id'),
                'purchase_date': verification.get('order_date')
            })
        else:
            return jsonify({
                'has_access': False,
                'message': verification.get('message', 'No valid purchase found')
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'WooCommerce Integration Webhook'
    })

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with service information."""
    return jsonify({
        'service': 'WooCommerce Integration Webhook',
        'version': '1.0.0',
        'endpoints': {
            'webhook': '/webhook/woocommerce',
            'check_access': '/api/check-access',
            'health': '/health'
        },
        'description': 'Handles WooCommerce webhooks and user provisioning for Rental Analytics app'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

