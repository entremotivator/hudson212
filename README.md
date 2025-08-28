# RentCast Property Analytics - WooCommerce Integration

This updated version of the RentCast Property Analytics app integrates with WooCommerce to automatically provision users based on product purchases.

## Key Changes Made

### 1. Removed Frontend Signup
- Removed the signup tab from the authentication interface
- Users can only login, not create accounts directly
- Added messaging directing users to purchase from WooCommerce store

### 2. WooCommerce Integration
- Added WooCommerce API integration for order verification
- Automatic user provisioning when item ID "i90" is purchased
- Webhook endpoint for real-time order processing
- Purchase verification system

### 3. WordPress Data Sync
- WordPress API integration for user data synchronization
- Automatic WordPress user creation when needed
- User data sync between WordPress and Supabase

### 4. Automatic User Provisioning
- Automatic Supabase user creation on order completion
- Secure password generation for new users
- User metadata storage including purchase information
- Email-based access verification

## Files Added/Modified

### New Files:
- `utils/woocommerce.py` - WooCommerce API integration
- `utils/wordpress.py` - WordPress API integration  
- `utils/user_provisioning.py` - User provisioning logic
- `webhook_server.py` - Streamlit-dependent webhook server
- `standalone_webhook.py` - Standalone Flask webhook server
- `README.md` - This documentation

### Modified Files:
- `utils/auth.py` - Updated login flow with auto-provisioning
- `requirements.txt` - Added new dependencies
- `.streamlit/secrets.toml` - Fixed configuration keys

## Configuration

### Required Environment Variables/Secrets

Update your `.streamlit/secrets.toml` file with:

```toml
[supabase]
url = "your-supabase-url"
anon_key = "your-supabase-anon-key"

[wordpress]
base_url = "https://aipropiq.com/"
username = "your-wordpress-username"
password = "your-wordpress-password"

[woocommerce]
consumer_key = "your-woocommerce-consumer-key"
consumer_secret = "your-woocommerce-consumer-secret"

[rentcast]
api_key = "your-rentcast-api-key"
```

### For Standalone Webhook Server

Set these environment variables:

```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_ANON_KEY="your-supabase-anon-key"
export WORDPRESS_BASE_URL="https://aipropiq.com/"
export WORDPRESS_USERNAME="your-wordpress-username"
export WORDPRESS_PASSWORD="your-wordpress-password"
export WOOCOMMERCE_CONSUMER_KEY="your-woocommerce-consumer-key"
export WOOCOMMERCE_CONSUMER_SECRET="your-woocommerce-consumer-secret"
```

## Deployment

### 1. Streamlit App

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### 2. Webhook Server

#### Option A: Streamlit-dependent (for development)
```bash
python webhook_server.py
```

#### Option B: Standalone (recommended for production)
```bash
python standalone_webhook.py
```

### 3. WooCommerce Webhook Configuration

In your WooCommerce admin:

1. Go to WooCommerce > Settings > Advanced > Webhooks
2. Create a new webhook with:
   - **Name**: User Provisioning
   - **Status**: Active
   - **Topic**: Order updated
   - **Delivery URL**: `https://your-domain.com/webhook/woocommerce`
   - **Secret**: (optional, for security)

## API Endpoints

### Webhook Server Endpoints:

- `POST /webhook/woocommerce` - Handles WooCommerce order webhooks
- `POST /api/check-access` - Check if user has purchase access
- `GET /health` - Health check endpoint
- `GET /` - Service information

### Example API Usage:

```bash
# Check user access
curl -X POST https://your-webhook-url/api/check-access \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

## How It Works

### User Flow:

1. **Purchase**: User purchases item ID "i90" from WooCommerce store
2. **Webhook**: WooCommerce sends webhook to your server on order completion
3. **Verification**: System verifies the purchase contains item "i90"
4. **Provisioning**: System creates Supabase user with secure password
5. **Notification**: User receives login credentials (implement email notification)
6. **Login**: User can now login to the app with their email and generated password

### Login Flow:

1. User enters email and password
2. System attempts normal login
3. If login fails, system checks WooCommerce for valid purchase
4. If purchase found, system auto-provisions user account
5. User is logged in automatically or given temporary credentials

## Security Considerations

1. **Webhook Security**: Consider implementing webhook signature verification
2. **Password Security**: Generated passwords are secure but should be changed by users
3. **API Keys**: Keep all API keys and secrets secure
4. **HTTPS**: Always use HTTPS in production
5. **Rate Limiting**: Consider implementing rate limiting on API endpoints

## Troubleshooting

### Common Issues:

1. **Circular Import Error**: Fixed by using dynamic imports in auth.py
2. **Secrets Not Found**: Ensure secrets.toml has correct key names
3. **Webhook Not Triggering**: Check WooCommerce webhook configuration
4. **User Not Created**: Check logs for API errors and credentials

### Logs:

- Webhook server logs all requests for debugging
- Check console output for error messages
- Verify API credentials are correct

## Testing

### Test Webhook Locally:

```bash
# Test health endpoint
curl http://localhost:5000/health

# Test access check
curl -X POST http://localhost:5000/api/check-access \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Test Streamlit App:

1. Start the app: `streamlit run app.py`
2. Try logging in with test credentials
3. Verify the signup tab is removed
4. Check the purchase link works

## Support

For issues or questions:

1. Check the logs for error messages
2. Verify all API credentials are correct
3. Test webhook endpoints manually
4. Check WooCommerce webhook delivery logs

## Next Steps

1. **Email Notifications**: Implement email sending for new user credentials
2. **Password Reset**: Add password reset functionality
3. **User Management**: Add admin interface for user management
4. **Analytics**: Add tracking for user provisioning success rates
5. **Security**: Implement webhook signature verification

