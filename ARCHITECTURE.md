# RevenueCat Integration Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MOBILE APP (iOS/Android)                        │
│                                                                          │
│  User selects plan → RevenueCat SDK → Apple/Google Play Store          │
│                                      ↓                                   │
│                          Purchase Completion                             │
└──────────────────────────────────────┬──────────────────────────────────┘
                                       │
                    ┌──────────────────┘
                    │
                    ↓
    ┌───────────────────────────────────────┐
    │      RevenueCat Backend               │
    │  (Cloud Verification Service)         │
    │                                        │
    │  - Verifies receipt with store         │
    │  - Stores transaction info             │
    │  - Sends webhook to your server ←──┐  │
    └───────────────────────────────────────┘
                    │                       │
                    │                       │
                    ↓                       │
    ┌───────────────────────────────────────┐
    │     Your Django Backend                │
    │                                        │
    │  A) Webhook Handler (Automatic)        │
    │     ├─ Receives events                 │
    │     ├─ Validates signature             │
    │     └─ Updates subscriptions           │
    │                                        │
    │  B) Verify Endpoint (Optional)         │
    │     ├─ POST /api/purchases/rc-verify   │
    │     ├─ Calls RevenueCat API            │
    │     └─ Activates subscription          │
    │                                        │
    │  Database Updates:                     │
    │  ├─ InAppPurchase record created      │
    │  ├─ Subscription record created       │
    │  ├─ User marked as premium            │
    │  └─ Transaction logged                 │
    └───────────────────────────────────────┘
                    │
                    ↓
    ┌───────────────────────────────────────┐
    │      Database (Django ORM)             │
    │                                        │
    │  Models Updated:                      │
    │  ├─ User (is_premium, free_scans)    │
    │  ├─ Subscription (status, end_date)  │
    │  └─ InAppPurchase (rc_transaction_id) │
    └───────────────────────────────────────┘
```

---

## Detailed Flow - Purchase Event

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. USER MAKES PURCHASE                                                 │
├────────────────────────────────────────────────────────────────────────┤
│ Mobile App → RevenueCat SDK → Apple App Store / Google Play             │
│                                         │                               │
│                                         ↓                               │
│                            [Store Processes Payment]                    │
│                                         │                               │
│                                         ↓                               │
│                          RevenueCat receives receipt                    │
│                          from App Store/Play Store                      │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 2. REVENUECAT VERIFIES & PROCESSES                                     │
├────────────────────────────────────────────────────────────────────────┤
│ RevenueCat:                                                             │
│  ✓ Validates receipt with Apple/Google                                 │
│  ✓ Extracts transaction details                                        │
│  ✓ Stores in RevenueCat database                                       │
│  ✓ Triggers webhook to your server                                     │
│  ✓ Updates customer record                                             │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 3. WEBHOOK RECEIVED BY DJANGO                                          │
├────────────────────────────────────────────────────────────────────────┤
│ POST /api/webhooks/revenuecat/                                         │
│ {                                                                        │
│   "event": {                                                            │
│     "type": "PURCHASE",                                                 │
│     "timestamp": "2025-02-04T12:00:00Z"                                │
│   },                                                                    │
│   "transaction": {                                                      │
│     "id": "rc_transaction_123",                                         │
│     "product_id": "premium_monthly",                                    │
│     "purchase_date": "2025-02-04T12:00:00Z",                           │
│     "expiration_date": "2025-03-04T12:00:00Z",                         │
│     "platform": "apple"                                                 │
│   },                                                                    │
│   "customer": {                                                         │
│     "app_user_id": "123"  ← Maps to Django User.id                    │
│   }                                                                     │
│ }                                                                       │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 4. DJANGO PROCESSES WEBHOOK                                            │
├────────────────────────────────────────────────────────────────────────┤
│ RevenueCatWebhookView:                                                  │
│                                                                          │
│  Step 1: Verify Signature                                              │
│  ┌─────────────────────────────────────┐                               │
│  │ HMAC-SHA256(request.body, secret)   │                               │
│  │ Compare with X-RevenueCat-...       │                               │
│  └─────────────────────────────────────┘                               │
│                ↓ (Verified ✓)                                           │
│                                                                          │
│  Step 2: Extract Event Type                                            │
│  ┌─────────────────────────────────────┐                               │
│  │ event_type = "PURCHASE"              │                               │
│  └─────────────────────────────────────┘                               │
│                ↓                                                         │
│                                                                          │
│  Step 3: Call Handler                                                  │
│  ┌─────────────────────────────────────┐                               │
│  │ revenuecat.handle_webhook(           │                               │
│  │   "PURCHASE",                        │                               │
│  │   webhook_data                       │                               │
│  │ )                                    │                               │
│  └─────────────────────────────────────┘                               │
│                ↓                                                         │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 5. PURCHASE HANDLER PROCESSES                                          │
├────────────────────────────────────────────────────────────────────────┤
│ _handle_purchase_event():                                              │
│                                                                          │
│  1. Extract product_id from webhook                                     │
│     product_id = "premium_monthly"                                     │
│                ↓                                                         │
│                                                                          │
│  2. Find corresponding Django SubscriptionPlan                          │
│     plan = SubscriptionPlan.objects.get(                               │
│       apple_product_id="premium_monthly"                               │
│     )                                                                   │
│                ↓                                                         │
│                                                                          │
│  3. Create/Update InAppPurchase record                                 │
│     InAppPurchase.objects.update_or_create(                            │
│       rc_transaction_id="rc_transaction_123",                          │
│       defaults={                                                        │
│         user=user,                                                      │
│         plan=plan,                                                      │
│         status="verified",                                              │
│         is_verified=True,                                               │
│         verified_at=now(),                                              │
│         rc_transaction_id="rc_transaction_123",                        │
│         ...                                                             │
│       }                                                                 │
│     )                                                                   │
│                ↓                                                         │
│                                                                          │
│  4. If new purchase, activate subscription                              │
│     subscription.activate()                                             │
│                ↓                                                         │
│     subscription.status = "active"                                      │
│     subscription.end_date = start_date + duration                      │
│     subscription.scans_remaining = plan.scans_included                │
│     subscription.save()                                                │
│                ↓                                                         │
│                                                                          │
│  5. Update user as premium                                              │
│     user.is_premium = True                                              │
│     user.subscription_type = plan.analysis_type                        │
│     user.free_scans_remaining = plan.scans_included                   │
│     user.save()                                                         │
│                ↓                                                         │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 6. DATABASE UPDATED                                                    │
├────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ ✓ InAppPurchase created with:                                          │
│   - rc_transaction_id (for tracking)                                    │
│   - status = "verified"                                                 │
│   - raw_response (full RC data)                                         │
│                                                                          │
│ ✓ Subscription created with:                                           │
│   - status = "active"                                                   │
│   - start_date = 2025-02-04                                            │
│   - end_date = 2025-03-04                                              │
│   - scans_remaining = 100 (from plan)                                   │
│                                                                          │
│ ✓ User updated with:                                                   │
│   - is_premium = True                                                   │
│   - subscription_type = "premium"                                       │
│   - free_scans_remaining = 100                                          │
│                                                                          │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 7. USER EXPERIENCE                                                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ Mobile App:                                                             │
│  ✓ Purchase completed                                                   │
│  ✓ Entitlements unlocked in RevenueCat SDK                             │
│  ✓ Premium features available                                           │
│                                                                          │
│ Your Backend:                                                           │
│  ✓ User is marked premium                                              │
│  ✓ Full analyses enabled                                               │
│  ✓ User can download reports, etc.                                     │
│                                                                          │
│ RevenueCat Dashboard:                                                   │
│  ✓ Purchase recorded                                                    │
│  ✓ Customer lifecycle tracked                                           │
│  ✓ Analytics updated                                                    │
│                                                                          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```sql
-- InAppPurchase (after migration)
┌──────────────────────────────────┐
│      InAppPurchase               │
├──────────────────────────────────┤
│ id                               │
│ user_id (FK → User)              │
│ plan_id (FK → SubscriptionPlan)  │
│ subscription_id (FK)             │
│ platform                         │
│ status                           │
│ purchase_date                    │
│ expiry_date                      │
│ is_verified                      │
│ verified_at                      │
├─ NEW FIELDS ─────────────────────┤
│ rc_transaction_id       ← RC ID  │
│ rc_customer_id          ← RC cust│
│ rc_entitlement_id       ← RC ent │
├──────────────────────────────────┤
│ created_at, updated_at           │
└──────────────────────────────────┘

-- Subscription (unchanged, but used)
┌──────────────────────────────────┐
│      Subscription                │
├──────────────────────────────────┤
│ id                               │
│ user_id (FK → User)              │
│ plan_id (FK → SubscriptionPlan)  │
│ status                           │
│ start_date                       │
│ end_date                         │
│ scans_remaining                  │
│ auto_renew                       │
├──────────────────────────────────┤
│ created_at, updated_at           │
└──────────────────────────────────┘

-- User (fields updated)
┌──────────────────────────────────┐
│         User                     │
├──────────────────────────────────┤
│ id                               │
│ email                            │
│ is_premium          ← Updated    │
│ subscription_type   ← Updated    │
│ free_scans_remaining← Updated    │
│ subscription_start_date          │
│ subscription_end_date            │
└──────────────────────────────────┘
```

---

## Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                    Your Architecture                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Mobile App ────────────────────────────────────────────────┐   │
│      │                                                       │   │
│      ├─ RevenueCat SDK Init         (MOBILE_INTEGRATION)    │   │
│      └─ Handle Purchase             (MOBILE_INTEGRATION)    │   │
│                                                              │   │
│  RevenueCat ─────────────────────────────────────────────┐  │   │
│      │                                                    │  │   │
│      ├─ Verify Receipt                                   │  │   │
│      ├─ Store Transaction                               │  │   │
│      └─ Send Webhook ──────────────────────────────────┐ │  │   │
│                                                         │ │  │   │
│  Django Backend ──────────────────────────────────────┐│ │  │   │
│      │                                                 ││ │  │   │
│      ├─ /api/webhooks/revenuecat/  ◄─────────────────┘│ │  │   │
│      │  (RevenueCatWebhookView)                       │ │  │   │
│      │                                                 │ │  │   │
│      ├─ /api/purchases/revenuecat-verify/  ◄──────────┘ │  │   │
│      │  (RevenueCatVerifyPurchaseAPIView)               │  │   │
│      │                                                  │  │   │
│      └─ Database Update                                 │  │   │
│         (Subscription, InAppPurchase, User)             │  │   │
│                                                         │  │   │
│  Services ────────────────────────────────────────────┐ │  │   │
│      │                                                 │ │  │   │
│      └─ RevenueCatService                             │ │  │   │
│         (revenuecat_service.py)                        │ │  │   │
│         ├─ create_or_update_customer()                │ │  │   │
│         ├─ verify_purchase()                          │ │  │   │
│         ├─ get_customer_info()                        │ │  │   │
│         ├─ process_subscription_from_rc()             │ │  │   │
│         └─ handle_webhook() + event handlers          │ │  │   │
│                                                        │ │  │   │
│         ├─ _handle_purchase_event()                   │ │  │   │
│         ├─ _handle_renewal_event()                    │ │  │   │
│         ├─ _handle_cancellation_event()               │ │  │   │
│         └─ _handle_expiration_event()                 │ │  │   │
│                                                        │ │  │   │
└────────────────────────────────────────────────────────┘ │  │   │
                                                           │  │   │
         ← External Services (Not in your code) ──────────┘  │   │
                                                              │   │
         See MOBILE_INTEGRATION_GUIDE.md ──────────────────────┘
```

---

## Event Lifecycle

```
User Makes Purchase
         │
         ↓
RevenueCat Receives + Verifies
         │
         ├─ PURCHASE EVENT (One-time) ─────────┐
         │                                      │
         ├─ RENEWAL EVENT (Recurring) ─────┐   │
         │                                  │   │
         ├─ CANCELLATION EVENT (User) ──┐  │   │
         │                               │  │   │
         └─ EXPIRATION EVENT (Timeout)──────────┐
                                       │  │   │  │
                                       ↓  ↓   ↓  ↓
                                    Django Handles Each
                                   Updates Subscription
                                   Updates User Status
```

---

## Summary

The RevenueCat integration provides:
1. **Secure verification** - No need to call Apple/Google directly
2. **Unified API** - One endpoint for iOS and Android
3. **Webhook events** - Automatic updates in real-time
4. **Customer management** - RevenueCat tracks lifecycle
5. **Analytics** - Built-in dashboard for metrics
