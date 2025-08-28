# Deployment Guide - RentCast WooCommerce Integration

## Quick Start

### 1. Update Configuration

Replace the placeholder values in `.streamlit/secrets.toml`:

```toml
[supabase]
url = "https://your-project.supabase.co"
anon_key = "your-actual-supabase-anon-key"

[wordpress]
base_url = "https://aipropiq.com/"
username = "your-actual-wordpress-username"
password = "your-actual-wordpress-password"

[woocommerce]
consumer_key = "ck_your-actual-consumer-key"
consumer_secret = "cs_your-actual-consumer-secret"

[rentcast]
api_key = "your-actual-rentcast-api-key"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Deploy Components

#### A. Streamlit App (Main Application)

```bash
# Local development
streamlit run app.py

# Or deploy to Streamlit Cloud
# 1. Push to GitHub
# 2. Connect to Streamlit Cloud
# 3. Add secrets in Streamlit Cloud dashboard
```

#### B. Webhook Server (for WooCommerce Integration)

**Option 1: Standalone Server (Recommended)**
```bash
# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-actual-supabase-anon-key"
export WORDPRESS_BASE_URL="https://aipropiq.com/"
export WORDPRESS_USERNAME="your-actual-wordpress-username"
export WORDPRESS_PASSWORD="your-actual-wordpress-password"
export WOOCOMMERCE_CONSUMER_KEY="ck_your-actual-consumer-key"
export WOOCOMMERCE_CONSUMER_SECRET="cs_your-actual-consumer-secret"

# Run the server
python standalone_webhook.py
```

**Option 2: Using a Platform (Heroku, Railway, etc.)**

Create a `Procfile`:
```
web: python standalone_webhook.py
```

Set environment variables in your platform's dashboard.

### 4. Configure WooCommerce Webhooks

1. Go to WooCommerce Admin → Settings → Advanced → Webhooks
2. Click "Create webhook"
3. Configure:
   - **Name**: User Provisioning
   - **Status**: Active  
   - **Topic**: Order updated
   - **Delivery URL**: `https://your-webhook-domain.com/webhook/woocommerce`
   - **API Version**: WC API v3
   - **Secret**: (optional, for additional security)

### 5. Test the Integration

#### Test Webhook Server:
```bash
curl https://your-webhook-domain.com/health
```

#### Test Access Check:
```bash
curl -X POST https://your-webhook-domain.com/api/check-access \
  -H "Content-Type: application/json" \
  -d '{"email": "customer@example.com"}'
```

#### Test Streamlit App:
1. Visit your Streamlit app URL
2. Verify signup tab is removed
3. Try logging in (should show purchase message for non-existing users)

## Production Deployment Options

### Option 1: Streamlit Cloud + Heroku

**Streamlit App on Streamlit Cloud:**
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Add secrets in Streamlit Cloud dashboard
4. Deploy

**Webhook Server on Heroku:**
1. Create Heroku app
2. Set environment variables
3. Deploy standalone_webhook.py
4. Configure WooCommerce webhook URL

### Option 2: VPS/Cloud Server

**Single Server Setup:**
```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip nginx

# Clone your repository
git clone your-repo-url
cd your-app

# Install Python dependencies
pip3 install -r requirements.txt

# Run with PM2 or systemd
# Streamlit app on port 8501
# Webhook server on port 5000

# Configure nginx reverse proxy
```

### Option 3: Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501 5000

CMD ["sh", "-c", "python standalone_webhook.py & streamlit run app.py --server.address 0.0.0.0"]
```

## Environment Variables Reference

### Required for Webhook Server:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `WORDPRESS_BASE_URL`
- `WORDPRESS_USERNAME`
- `WORDPRESS_PASSWORD`
- `WOOCOMMERCE_CONSUMER_KEY`
- `WOOCOMMERCE_CONSUMER_SECRET`

### Optional:
- `PORT` (default: 5000 for webhook server)

## Security Checklist

- [ ] All API keys are secure and not in version control
- [ ] Webhook server uses HTTPS in production
- [ ] WooCommerce webhook secret is configured (optional)
- [ ] Supabase RLS policies are properly configured
- [ ] WordPress user has minimal required permissions
- [ ] Server firewall is properly configured

## Monitoring and Maintenance

### Health Checks:
- Webhook server: `GET /health`
- Streamlit app: Check if login page loads

### Logs to Monitor:
- Webhook server console output
- WooCommerce webhook delivery logs
- Supabase auth logs
- Streamlit app logs

### Regular Tasks:
- Monitor webhook delivery success rate
- Check for failed user provisioning attempts
- Update dependencies regularly
- Backup Supabase data

## Troubleshooting

### Webhook Not Working:
1. Check WooCommerce webhook delivery logs
2. Verify webhook URL is accessible
3. Check webhook server logs
4. Test webhook endpoint manually

### User Not Created:
1. Check webhook server logs for errors
2. Verify Supabase credentials
3. Check if order contains item ID "i90"
4. Verify WooCommerce API credentials

### Login Issues:
1. Check Supabase auth logs
2. Verify user exists in Supabase
3. Check if purchase verification is working
4. Test with known good credentials

### API Errors:
1. Verify all API credentials
2. Check API rate limits
3. Ensure proper API permissions
4. Test API endpoints individually

## Support

If you encounter issues:

1. Check the logs first
2. Verify all credentials are correct
3. Test each component individually
4. Check the troubleshooting section above

For additional help, provide:
- Error messages from logs
- Steps to reproduce the issue
- Configuration details (without sensitive data)

