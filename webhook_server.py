from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime

# Add the current directory to Python path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.user_provisioning import verify_and_provision_user, check_user_access_status

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
                # Provision user access
                result = verify_and_provision_user(customer_email)
                
                if result.get('success'):
                    return jsonify({
                        'status': 'success',
                        'message': 'User provisioned successfully',
                        'user_created': not result.get('exists', False),
                        'email': customer_email,
                        'order_id': order_id
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': result.get('message', 'Unknown error'),
                        'email': customer_email,
                        'order_id': order_id
                    }), 500
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
        
        access_status = check_user_access_status(email)
        return jsonify(access_status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/provision-user', methods=['POST'])
def provision_user():
    """API endpoint to manually provision a user."""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        result = verify_and_provision_user(email)
        return jsonify(result)
        
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
            'provision_user': '/api/provision-user',
            'health': '/health'
        },
        'description': 'Handles WooCommerce webhooks and user provisioning for Rental Analytics app'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

