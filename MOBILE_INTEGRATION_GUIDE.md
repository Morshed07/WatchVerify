# RevenueCat Integration for Mobile Developers

## iOS Implementation

### 1. Install RevenueCat SDK
```swift
// In your Podfile
pod 'RevenueCat'
```

### 2. Configure in AppDelegate
```swift
import RevenueCat

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Configure RevenueCat
        Purchases.logLevel = .debug
        Purchases.configure(withAPIKey: "your_public_api_key")
        
        return true
    }
}
```

### 3. Get Offerings and Display Paywall
```swift
import RevenueCat

class SubscriptionViewController: UIViewController {
    
    func displaySubscriptions() {
        Purchases.shared.offerings { [weak self] offerings, error in
            guard let offering = offerings?.current, error == nil else {
                print("Error fetching offerings: \(error?.localizedDescription ?? "Unknown")")
                return
            }
            
            // Display packages
            for package in offering.availablePackages {
                print("\(package.localizedTitle): \(package.localizedPriceString)")
            }
        }
    }
    
    func purchasePackage(_ package: Package) {
        Purchases.shared.purchase(package: package) { [weak self] transaction, customerInfo, error, cancelled in
            if cancelled {
                print("Purchase cancelled")
                return
            }
            
            if let error = error {
                print("Purchase error: \(error.localizedDescription)")
                return
            }
            
            // Verify with backend
            self?.verifyPurchaseWithBackend(customerInfo: customerInfo)
        }
    }
    
    func verifyPurchaseWithBackend(customerInfo: CustomerInfo) {
        // Optional: Verify with your backend
        // Your backend will also receive webhook from RevenueCat
        let userData = [
            "platform": "apple",
            "product_id": customerInfo.entitlements.active.first?.key ?? ""
        ]
        
        // Send to backend if needed
        // But webhook is the main verification method
    }
}
```

### 4. Check Entitlements
```swift
func checkPremiumAccess() {
    Purchases.shared.customerInfo { customerInfo, error in
        let hasPremium = customerInfo?.entitlements["premium"]?.isActive ?? false
        
        if hasPremium {
            print("User has premium access")
        } else {
            print("User needs premium")
        }
    }
}
```

---

## Android Implementation

### 1. Install RevenueCat SDK
```gradle
// In app/build.gradle
dependencies {
    implementation 'com.revenuecat.purchases:purchases:7.x.x'
}
```

### 2. Initialize in MainActivity
```kotlin
import com.revenuecat.purchases.Purchases
import com.revenuecat.purchases.LogLevel

class MainActivity : AppCompatActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Configure RevenueCat
        Purchases.logLevel = LogLevel.DEBUG
        Purchases.configure(
            Purchases.PurchasesConfiguration.Builder(this, "your_public_api_key")
                .build()
        )
    }
}
```

### 3. Get Offerings
```kotlin
fun displaySubscriptions() {
    Purchases.sharedInstance.getOfferings(
        { offerings ->
            val current = offerings.current
            current?.availablePackages?.forEach { package ->
                val title = package.product.title
                val price = package.product.price
                println("$title: $price")
            }
        },
        { error ->
            println("Error: ${error.message}")
        }
    )
}
```

### 4. Make Purchase
```kotlin
fun purchasePackage(activity: Activity, package: Package) {
    Purchases.sharedInstance.purchase(
        activity,
        package,
        { product, customerInfo ->
            // Purchase successful
            verifyPurchaseWithBackend(customerInfo)
        },
        { error ->
            println("Purchase error: ${error.message}")
        }
    )
}

private fun verifyPurchaseWithBackend(customerInfo: CustomerInfo) {
    // Optional: Notify backend
    // Webhook provides main verification
}
```

### 5. Check Entitlements
```kotlin
fun checkPremiumAccess() {
    Purchases.sharedInstance.getCustomerInfo(
        { customerInfo ->
            val hasPremium = customerInfo.entitlements["premium"]?.isActive == true
            
            if (hasPremium) {
                println("User has premium")
            } else {
                println("Need premium")
            }
        },
        { error ->
            println("Error: ${error.message}")
        }
    )
}
```

---

## Backend Verification (Optional)

After purchase, optionally notify your backend:

```swift
// iOS
func notifyBackendOfPurchase(customerInfo: CustomerInfo) {
    guard let token = customerInfo.allPurchases.first?.transactionIdentifier else { return }
    
    var request = URLRequest(url: URL(string: "https://yourdomain.com/api/purchases/revenuecat-verify/")!)
    request.httpMethod = "POST"
    request.addValue("application/json", forHTTPHeaderField: "Content-Type")
    request.addValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
    
    let body: [String: Any] = [
        "platform": "apple",
        "product_id": "premium_monthly",
        "receipt_data": token
    ]
    
    request.httpBody = try? JSONSerialization.data(withJSONObject: body)
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        // Handle response
    }.resume()
}
```

```kotlin
// Android
fun notifyBackendOfPurchase(customerInfo: CustomerInfo) {
    val client = OkHttpClient()
    val json = JSONObject().apply {
        put("platform", "google")
        put("product_id", "premium_monthly")
        put("purchase_token", "token_from_google")
    }
    
    val request = Request.Builder()
        .url("https://yourdomain.com/api/purchases/revenuecat-verify/")
        .header("Authorization", "Bearer $jwtToken")
        .post(RequestBody.create(json.toString().toMediaType()))
        .build()
    
    client.newCall(request).enqueue(object : Callback {
        override fun onFailure(call: Call, e: IOException) {}
        override fun onResponse(call: Call, response: Response) {}
    })
}
```

---

## Important Notes

### ✅ Do's
- ✓ Initialize RevenueCat early in app lifecycle
- ✓ Handle subscription status changes gracefully
- ✓ Show paywall for non-premium users
- ✓ Check entitlements before unlocking premium features
- ✓ Handle network errors gracefully

### ❌ Don'ts
- ✗ Don't rely only on client-side checks for access control
- ✗ Don't skip error handling
- ✗ Don't use test product IDs in production
- ✗ Don't ignore sandbox vs production modes

---

## Testing

### iOS Sandbox Testing
1. Configure test Apple ID in Settings → App Store
2. Use test subscription for purchases
3. Subscriptions renew every 3 minutes in sandbox

### Android Testing
1. Add test account in Google Play Console
2. Use internal testing track
3. Purchases use test accounts, not real payment

---

## Debugging

### Enable Debug Logging
```swift
// iOS
Purchases.logLevel = .verbose
```

```kotlin
// Android
Purchases.logLevel = LogLevel.VERBOSE
```

Check logs for:
- API key validation
- Purchase flow
- Entitlement updates
- Network requests

---

## RevenueCat Dashboard

Monitor purchases and users:
1. https://app.revenuecat.com
2. Dashboard shows real-time metrics
3. Test webhook delivery
4. View customer details
5. Check subscription status

---

## Support

For issues:
1. Check RevenueCat logs in dashboard
2. Check mobile app logs for SDK errors
3. Verify API key is correct
4. Ensure product IDs match configuration
5. Test with RevenueCat example app
