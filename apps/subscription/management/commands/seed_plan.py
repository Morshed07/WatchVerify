from django.core.management.base import BaseCommand
from apps.subscription.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Seed subscription plans matching your UI structure'
    
    def handle(self, *args, **kwargs):
        
        self.stdout.write(self.style.SUCCESS('\n🔧 Seeding Subscription Plans...\n'))
        
        plans = [
            # ==================== FREE PLAN ====================
            {
                'name': 'Free Plan',
                'category': 'free',
                'price': 0.00,
                'duration_days': None,
                'scans_included': 3,
                'sort_order': 0,
                'google_product_id': None,
                'apple_product_id': None,
                
                'analysis_type': 'basic',
                'basic_authenticity_check': True,
                'fast_processing': False,
                'show_component_breakdown': False,
                'show_component_observations': False,
                'component_detail_level': 0,
                'show_watch_information': False,
                'show_expert_notes': False,
                'show_confidence_metrics': False,
                'can_download_pdf': False,
                'pdf_includes_stamps': False,
                'pdf_is_bilingual': False,
                'includes_price_estimation': False,
                'priority_processing': False,
                'priority_support': False,
                'unlimited_analyses': False,
            },
            
            # ==================== PAY-PER-SCAN ====================
            
            # Standard Analysis - $2.49
            {
                'name': 'Standard Analysis',
                'category': 'pay_per_scan',
                'description': 'Basic authenticity check with fast processing',
                'price': 2.49,
                'duration_days': 1,
                'scans_included': 1,
                'sort_order': 1,
                'google_product_id': 'standard_analysis',
                'apple_product_id': 'com.watchauth.standard',
                
                'analysis_type': 'standard',
                'basic_authenticity_check': True,
                'fast_processing': True,
                'show_component_breakdown': False,  # No component details
                'show_component_observations': False,
                'component_detail_level': 0,
                'show_watch_information': True,  # Basic watch info
                'show_expert_notes': False,
                'show_confidence_metrics': False,
                'can_download_pdf': False,
                'pdf_includes_stamps': False,
                'pdf_is_bilingual': False,
                'includes_price_estimation': False,
                'priority_processing': False,
                'priority_support': False,
                'unlimited_analyses': False,
            },
            
            # Premium Analysis - $5.49
            {
                'name': 'Premium Analysis',
                'category': 'pay_per_scan',
                'description': 'Detailed AI breakdown with all components evaluated',
                'price': 5.49,
                'duration_days': 1,
                'scans_included': 1,
                'sort_order': 2,
                'google_product_id': 'premium_analysis',
                'apple_product_id': 'com.watchauth.premium_analysis',
                
                'analysis_type': 'premium',
                'basic_authenticity_check': True,
                'fast_processing': True,
                'show_component_breakdown': True,  # ✓ Component breakdown
                'show_component_observations': True,  # ✓ Observations
                'component_detail_level': 2,  # Scores + Brief observations
                'show_watch_information': True,
                'show_expert_notes': True,  # ✓ Expert notes
                'show_confidence_metrics': True,  # ✓ Statistics
                'can_download_pdf': True,  # ✓ PDF report
                'pdf_includes_stamps': True,  # ✓ With stamps
                'pdf_is_bilingual': True,
                'includes_price_estimation': False,
                'priority_processing': False,
                'priority_support': False,
                'unlimited_analyses': False,
            },
            
            # ==================== PREMIUM SUBSCRIPTION ====================
            
            # Premium Monthly - $11.99
            {
                'name': 'Premium Monthly',
                'category': 'premium',
                'description': 'Up to 100 analyses per month with full features',
                'price': 11.99,
                'duration_days': 30,
                'scans_included': 0,  # Unlimited
                'sort_order': 3,
                'google_product_id': 'premium_monthly',
                'apple_product_id': 'com.watchauth.premium.monthly',
                
                'analysis_type': 'premium',
                'basic_authenticity_check': True,
                'fast_processing': True,
                'show_component_breakdown': True,
                'show_component_observations': True,
                'component_detail_level': 2,
                'show_watch_information': True,
                'show_expert_notes': True,
                'show_confidence_metrics': True,
                'can_download_pdf': True,
                'pdf_includes_stamps': False,  # No stamps
                'pdf_is_bilingual': True,
                'includes_price_estimation': False,
                'priority_processing': True,  # ✓ Priority queue
                'priority_support': False,
                'unlimited_analyses': True,  # ✓ Unlimited
            },
            
            # Premium Yearly - $89.99 (Save 37%)
            {
                'name': 'Premium Yearly',
                'category': 'premium',
                'description': 'Up to 100 analyses per month - Save 37%',
                'price': 89.99,
                'duration_days': 365,
                'scans_included': 0,
                'sort_order': 4,
                'google_product_id': 'premium_yearly',
                'apple_product_id': 'com.watchauth.premium.yearly',
                
                'analysis_type': 'premium',
                'basic_authenticity_check': True,
                'fast_processing': True,
                'show_component_breakdown': True,
                'show_component_observations': True,
                'component_detail_level': 2,
                'show_watch_information': True,
                'show_expert_notes': True,
                'show_confidence_metrics': True,
                'can_download_pdf': True,
                'pdf_includes_stamps': False,
                'pdf_is_bilingual': True,
                'includes_price_estimation': False,
                'priority_processing': True,
                'priority_support': False,
                'unlimited_analyses': True,
            },
            
            # ==================== PREMIUM UNLIMITED ====================
            
            # Premium Unlimited Monthly - $19.99
            {
                'name': 'Premium Unlimited Monthly',
                'category': 'unlimited',
                'description': 'Unlimited AI-powered analyses with full use policy',
                'price': 19.99,
                'duration_days': 30,
                'scans_included': 0,
                'sort_order': 5,
                'google_product_id': 'unlimited_monthly',
                'apple_product_id': 'com.watchauth.unlimited.monthly',
                
                'analysis_type': 'ultimate',
                'basic_authenticity_check': True,
                'fast_processing': True,
                'show_component_breakdown': True,
                'show_component_observations': True,
                'component_detail_level': 3,  # ✓ Full details
                'show_watch_information': True,
                'show_expert_notes': True,
                'show_confidence_metrics': True,
                'can_download_pdf': True,
                'pdf_includes_stamps': True,  # ✓ Official stamps
                'pdf_is_bilingual': True,
                'includes_price_estimation': True,  # ✓ Price estimation
                'priority_processing': True,
                'priority_support': True,  # ✓ Priority support
                'unlimited_analyses': True,
            },
            
            # Premium Unlimited Yearly - $159.99 (Save 33%)
            {
                'name': 'Premium Unlimited Yearly',
                'category': 'unlimited',
                'description': 'Unlimited AI-powered analyses - Save 33%',
                'price': 159.99,
                'duration_days': 365,
                'scans_included': 0,
                'sort_order': 6,
                'google_product_id': 'unlimited_yearly',
                'apple_product_id': 'com.watchauth.unlimited.yearly',
                
                'analysis_type': 'ultimate',
                'basic_authenticity_check': True,
                'fast_processing': True,
                'show_component_breakdown': True,
                'show_component_observations': True,
                'component_detail_level': 3,
                'show_watch_information': True,
                'show_expert_notes': True,
                'show_confidence_metrics': True,
                'can_download_pdf': True,
                'pdf_includes_stamps': True,
                'pdf_is_bilingual': True,
                'includes_price_estimation': True,
                'priority_processing': True,
                'priority_support': True,
                'unlimited_analyses': True,
            },
        ]
        
        # Create or update plans
        created_count = 0
        updated_count = 0
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                google_product_id=plan_data.get('google_product_id') or f"free_{plan_data['name'].lower().replace(' ', '_')}",
                defaults=plan_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created: {plan.name} - ${plan.price}')
                )
            else:
                updated_count += 1
                self.stdout.write(f'  ↻ Updated: {plan.name}')
            
            # Show features
            features = plan.get_feature_summary()
            for feature in features:
                self.stdout.write(f'      • {feature}')
            self.stdout.write('')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Complete! Created {created_count}, Updated {updated_count} plans\n'
            )
        )
