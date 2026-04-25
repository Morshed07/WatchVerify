# RevenueCat Integration - Setup Checklist

## Pre-Setup Requirements
- [ ] Django project running
- [ ] Database configured
- [ ] API authentication (JWT) working
- [ ] `.env` file created

---

## Step 1: RevenueCat Account Setup

### Create Account
- [ ] Visit https://www.revenuecat.com
- [ ] Click "Get Started Free"
- [ ] Sign up with email/Google
- [ ] Verify email

### Create Project
- [ ] Go to dashboard
- [ ] Click "Create Project"
- [ ] Enter project name
- [ ] Select region closest to users

### Add Apps
- [ ] Add iOS app
  - [ ] Bundle ID: `com.yourcompany.watchauth`
  - [ ] App Store ID: (from App Store Connect)
- [ ] Add Android app
  - [ ] Package name: `com.yourcompany.watchauth`
  - [ ] Google Play Store ID: (from Play Console)

### Get API Keys
- [ ] Click "Project Settings"
- [ ] Go to "API Keys"
- [ ] Copy "Public API Key" → Save to safe location
- [ ] Copy "Secret Key" → Save to safe location

---

## Step 2: Configure Products

### In RevenueCat Dashboard
- [ ] Go to "Products"
- [ ] Create product: `premium_monthly`
  - [ ] Type: Subscription
  - [ ] Duration: 1 month
  - [ ] Configure for iOS (set App Store ID)
  - [ ] Configure for Android (set Google Play ID)
- [ ] Create product: `premium_yearly`
  - [ ] Type: Subscription
  - [ ] Duration: 1 year
  - [ ] Configure for both platforms
- [ ] Repeat for other plans in your app

### Verify in Django
- [ ] Check `SubscriptionPlan` table
- [ ] Ensure `google_product_id` matches RevenueCat Google product
- [ ] Ensure `apple_product_id` matches RevenueCat Apple product

Example:
```python
# In Django admin or shell
SubscriptionPlan.objects.get(name="Premium Monthly").google_product_id
# Should match: "premium_monthly" in RevenueCat
```

---

## Step 3: Configure Django Backend

### Update .env File
```bash
# Add these lines to your .env file
REVENUECAT_API_KEY=pk_your_actual_key_here
REVENUECAT_SECRET_KEY=sk_your_actual_secret_here
```

- [ ] Add both keys to `.env`
- [ ] Verify keys are NOT in code
- [ ] `.env` is in `.gitignore`

### Run Migrations
```bash
python manage.py makemigrations payment
python manage.py migrate payment
```

- [ ] Run migration command
- [ ] Verify no errors
- [ ] Check database has new RC fields:
  ```bash
  python manage.py dbshell
  # SELECT rc_transaction_id FROM payment_inapppurchase LIMIT 1;
  ```

### Verify Settings
```bash
python manage.py shell
from django.conf import settings
print(settings.REVENUECAT_API_KEY)  # Should print your key
print(settings.REVENUECAT_SECRET_KEY)  # Should print your secret
```

- [ ] Check API keys are loaded in settings
- [ ] Keys are not None or empty
- [ ] Keys are valid

---

## Step 4: Configure Webhooks

### In RevenueCat Dashboard
- [ ] Go to "Project Settings"
- [ ] Click "Webhooks"
- [ ] Click "Add Webhook"
- [ ] Set URL:
  ```
  https://yourdomain.com/api/webhooks/revenuecat/
  ```
  (Replace `yourdomain.com` with your actual domain)

### Configure Events
Select all events:
- [ ] PURCHASE
- [ ] RENEWAL
- [ ] EXPIRATION
- [ ] CANCELLATION

### Get Signing Secret
- [ ] Copy the "Signing Secret" shown
- [ ] Make sure it matches your `.env` `REVENUECAT_SECRET_KEY`
- [ ] If different, update your `.env` with the correct secret
- [ ] Restart Django server

### Test Webhook Connection
- [ ] Click "Test Event" in RevenueCat
- [ ] Check your Django logs:
  ```
  INFO apps.payment.webhook Webhook processed: PURCHASE
  ```
- [ ] If error, check:
  - [ ] Domain is accessible from internet
  - [ ] Secret key matches exactly
  - [ ] Django is running

---

## Step 5: Test Backend Endpoint

### Test Webhook Reception
```bash
# Option 1: Use RevenueCat Test Event
# In dashboard, click "Test Event" for any webhook

# Option 2: Use curl to test locally (if you have ngrok)
curl -X POST http://localhost:8000/api/webhooks/revenuecat/ \
  -H "X-RevenueCat-Content-Signature: test" \
  -H "Content-Type: application/json" \
  -d '{
    "event": {"type": "PURCHASE"},
    "customer": {"app_user_id": "1"}
  }'
```

- [ ] Webhook received in logs
- [ ] No 401/403 errors
- [ ] 200 OK response

### Test Verify Endpoint
```bash
# Get a JWT token first
curl -X POST http://localhost:8000/api/auth/login/ \
  -d "email=test@example.com&password=password"

# Then test verify endpoint
curl -X POST http://localhost:8000/api/purchases/revenuecat-verify/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "apple",
    "product_id": "premium_monthly",
    "receipt_data": "test_receipt"
  }'
```

- [ ] Returns 200/201 on success
- [ ] Returns 400 on invalid input
- [ ] Check database for created records

---

## Step 6: Mobile Integration

### Share with Teams
- [ ] Send `MOBILE_INTEGRATION_GUIDE.md` to iOS team
- [ ] Send `MOBILE_INTEGRATION_GUIDE.md` to Android team
- [ ] Schedule integration kickoff meeting

### iOS Team
- [ ] Add RevenueCat pod: `pod 'RevenueCat'`
- [ ] Import and initialize RevenueCat SDK
- [ ] Configure with same API key
- [ ] Test in App Store Connect sandbox
- [ ] Monitor webhook receipt in backend

### Android Team
- [ ] Add RevenueCat dependency
- [ ] Import and initialize RevenueCat SDK
- [ ] Configure with same API key
- [ ] Test in Play Store internal testing
- [ ] Monitor webhook receipt in backend

---

## Step 7: Testing & QA

### Database Verification
```bash
python manage.py shell
from apps.payment.models import InAppPurchase
from apps.subscription.models import Subscription

# Check a purchase record
p = InAppPurchase.objects.latest('created_at')
print(f"Purchase: {p.id}")
print(f"RC Transaction: {p.rc_transaction_id}")
print(f"Status: {p.status}")
print(f"Verified: {p.is_verified}")

# Check subscription
s = Subscription.objects.filter(user__id=1).latest('created_at')
print(f"Subscription: {s.id}")
print(f"Status: {s.status}")
print(f"End Date: {s.end_date}")

# Check user premium status
from apps.user.models import User
u = User.objects.get(id=1)
print(f"Is Premium: {u.is_premium}")
print(f"Subscription Type: {u.subscription_type}")
```

- [ ] Records created in database
- [ ] RC transaction ID populated
- [ ] Status is "verified"
- [ ] User marked as premium
- [ ] Dates are correct

### Log Verification
```bash
# Check Django logs for service calls
grep -i "revenuecat" /path/to/django.log
grep -i "webhook processed" /path/to/django.log
```

- [ ] Service initialization logged
- [ ] Webhook events processed
- [ ] No error messages
- [ ] Timestamps make sense

### End-to-End Test
- [ ] iOS: Make test purchase
- [ ] Android: Make test purchase
- [ ] Check RevenueCat dashboard
- [ ] Wait for webhook (usually <10 seconds)
- [ ] Check Django logs
- [ ] Verify database updated
- [ ] Check user premium status changed

---

## Step 8: Staging Deployment

### Pre-Deploy Checklist
- [ ] All tests passing
- [ ] No hardcoded API keys
- [ ] `.env` configured
- [ ] Migrations applied
- [ ] Webhook URL updated to staging domain
- [ ] SSL certificate valid for domain

### Deploy
```bash
git add -A
git commit -m "Add RevenueCat integration"
git push origin main
# Deploy to staging server
```

- [ ] Code deployed
- [ ] `.env` updated on server
- [ ] Migrations run: `python manage.py migrate`
- [ ] Django restarted

### Verify on Staging
- [ ] Make test purchase on staging
- [ ] Check webhook received
- [ ] Verify database record created
- [ ] Check all logs clean

---

## Step 9: Production Deployment

### Final Checklist
- [ ] Staging tests passed
- [ ] RevenueCat webhook URL updated to production domain
- [ ] SSL certificate valid
- [ ] `.env` secrets configured on production
- [ ] Database backups created
- [ ] Rollback plan documented
- [ ] Team on-call for monitoring

### Deploy
```bash
# Deploy to production
# (Your deployment process)
```

- [ ] Code deployed
- [ ] Migrations applied
- [ ] Django restarted
- [ ] Health check passed

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Watch RevenueCat dashboard
- [ ] Test with small purchase first
- [ ] Scale up after confidence
- [ ] Notify teams it's live

---

## Step 10: Ongoing Monitoring

### Daily Checks
- [ ] [ ] RevenueCat dashboard - any errors?
- [ ] [ ] Django logs - any issues?
- [ ] [ ] Database - records being created?
- [ ] [ ] Webhook - events being processed?

### Weekly Checks
- [ ] [ ] Review revenue metrics
- [ ] [ ] Check subscription renewal rate
- [ ] [ ] Review failed transactions
- [ ] [ ] Check customer complaints

### Monthly Checks
- [ ] [ ] Analyze subscription trends
- [ ] [ ] Update product pricing if needed
- [ ] [ ] Review feature usage
- [ ] [ ] Plan improvements

---

## Troubleshooting During Setup

### API Keys Not Loading
**Symptom**: "RevenueCat API keys not configured"

**Steps**:
1. [ ] Check `.env` file exists
2. [ ] Check keys are spelled correctly
3. [ ] Check `.env` is readable
4. [ ] Check Django is reading `.env`
   ```bash
   python manage.py shell
   from django.conf import settings
   print(settings.REVENUECAT_API_KEY)
   ```
5. [ ] Restart Django server
6. [ ] Check for typos in keys

### Migration Fails
**Symptom**: Migration error when running `migrate payment`

**Steps**:
1. [ ] Check you ran `makemigrations` first
2. [ ] Check no syntax errors in models
3. [ ] Try: `python manage.py migrate payment --fake-initial`
4. [ ] Check database connection
5. [ ] Check migrations folder has `__init__.py`

### Webhook Not Received
**Symptom**: Webhook sent but Django doesn't get it

**Steps**:
1. [ ] Check domain is accessible from internet
   ```bash
   curl https://yourdomain.com/api/webhooks/revenuecat/
   ```
2. [ ] Check SSL certificate is valid
3. [ ] Check Django logs for errors
4. [ ] Check secret key matches exactly
5. [ ] Check firewall allows incoming traffic
6. [ ] Test with ngrok if local testing
   ```bash
   # Install ngrok, then
   ngrok http 8000
   # Use ngrok URL in webhook config
   ```

### Product ID Mismatch
**Symptom**: "No subscription plan found for product"

**Steps**:
1. [ ] List all plans in Django:
   ```bash
   python manage.py shell
   from apps.subscription.models import SubscriptionPlan
   for p in SubscriptionPlan.objects.all():
       print(f"{p.name}: {p.google_product_id}, {p.apple_product_id}")
   ```
2. [ ] List products in RevenueCat dashboard
3. [ ] Ensure IDs match exactly (case-sensitive!)
4. [ ] Update Django plan IDs if needed

---

## Quick Reference

### Important Commands
```bash
# Run migrations
python manage.py migrate payment

# Test in shell
python manage.py shell

# Check logs
tail -f /path/to/django.log
grep revenuecat /path/to/django.log

# Verify settings
python -c "from django.conf import settings; print(settings.REVENUECAT_API_KEY)"
```

### Important URLs
- RevenueCat Dashboard: https://app.revenuecat.com
- Project Settings: https://app.revenuecat.com → Project Settings
- Webhooks: Project Settings → Webhooks
- Products: Project Settings → Products

### Important Files
- Backend service: `apps/payment/revenuecat_service.py`
- Webhook handler: `apps/payment/webhook.py`
- Views: `apps/payment/views.py`
- Settings: `chronoverify/settings.py`
- Models: `apps/payment/models.py`

---

## When Complete

✅ All checkboxes above checked
✅ No errors in logs
✅ Test purchase successful
✅ Database has records
✅ RevenueCat dashboard updated
✅ Production receiving webhooks
✅ Team trained on system
✅ Monitoring in place

## 🎉 You're Done!

Your RevenueCat integration is complete and ready for production!
