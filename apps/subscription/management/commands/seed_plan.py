from django.core.management.base import BaseCommand
from apps.subscription.models import SubscriptionPlan
from django.db import transaction


class Command(BaseCommand):
    help = 'Seed all subscription plans in English and French'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n🔧 Seeding Subscription Plans (EN + FR)...\n'))

        base_plans = [
            # ==================== FREE PLAN ====================
            {
                'name': {'en': 'Free Plan', 'fr': 'Plan Gratuit'},
                'description': {'en': '', 'fr': ''},
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
            {
                'name': {'en': 'Standard Analysis', 'fr': 'Analyse Standard'},
                'description': {'en': 'Basic authenticity check with fast processing',
                                'fr': 'Vérification basique d\'authenticité avec traitement rapide'},
                'category': 'pay_per_scan',
                'price': 2.49,
                'duration_days': 1,
                'scans_included': 1,
                'sort_order': 1,
                'google_product_id': None,
                'apple_product_id': None,
                'analysis_type': 'standard',
                'basic_authenticity_check': True,
                'fast_processing': True,
                'show_component_breakdown': False,
                'show_component_observations': False,
                'component_detail_level': 0,
                'show_watch_information': True,
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
            {
                'name': {'en': 'Premium Analysis', 'fr': 'Analyse Premium'},
                'description': {'en': 'Detailed AI breakdown with all components evaluated',
                                'fr': 'Analyse détaillée par IA avec tous les composants évalués'},
                'category': 'pay_per_scan',
                'price': 5.49,
                'duration_days': 1,
                'scans_included': 1,
                'sort_order': 2,
                'google_product_id': None,
                'apple_product_id': None,
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
                'pdf_includes_stamps': True,
                'pdf_is_bilingual': True,
                'includes_price_estimation': False,
                'priority_processing': False,
                'priority_support': False,
                'unlimited_analyses': False,
            },

            # ==================== PREMIUM SUBSCRIPTION ====================
            {
                'name': {'en': 'Premium Monthly', 'fr': 'Premium Mensuel'},
                'description': {'en': 'Up to 100 analyses per month with full features',
                                'fr': 'Jusqu\'à 100 analyses par mois avec toutes les fonctionnalités'},
                'category': 'premium',
                'price': 11.99,
                'duration_days': 30,
                'scans_included': 0,
                'sort_order': 3,
                'google_product_id': None,
                'apple_product_id': None,
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
            {
                'name': {'en': 'Premium Yearly', 'fr': 'Premium Annuel'},
                'description': {'en': 'Up to 100 analyses per month - Save 37%',
                                'fr': 'Jusqu\'à 100 analyses par mois - Économisez 37%'},
                'category': 'premium',
                'price': 89.99,
                'duration_days': 365,
                'scans_included': 0,
                'sort_order': 4,
                'google_product_id': None,
                'apple_product_id': None,
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
            {
                'name': {'en': 'Premium Unlimited Monthly', 'fr': 'Premium Illimité Mensuel'},
                'description': {'en': 'Unlimited AI-powered analyses with full use policy',
                                'fr': 'Analyses illimitées par IA avec toutes les fonctionnalités'},
                'category': 'unlimited',
                'price': 19.99,
                'duration_days': 30,
                'scans_included': 0,
                'sort_order': 5,
                'google_product_id': None,
                'apple_product_id': None,
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
            {
                'name': {'en': 'Premium Unlimited Yearly', 'fr': 'Premium Illimité Annuel'},
                'description': {'en': 'Unlimited AI-powered analyses - Save 33%',
                                'fr': 'Analyses illimitées par IA - Économisez 33%'},
                'category': 'unlimited',
                'price': 159.99,
                'duration_days': 365,
                'scans_included': 0,
                'sort_order': 6,
                'google_product_id': None,
                'apple_product_id': None,
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

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for plan_data in base_plans:
                for lang_code in ['en', 'fr']:
                    name = plan_data['name'][lang_code]
                    description = plan_data['description'][lang_code]
                    google_id = plan_data.get('google_product_id') or f"{lang_code}_{name.lower().replace(' ', '_')}"

                    plan, created = SubscriptionPlan.objects.update_or_create(
                        name=name,
                        language=lang_code,
                        category=plan_data['category'],
                        defaults={
                            **plan_data,
                            'name': name,
                            'description': description,
                            'language': lang_code,
                            'google_product_id': google_id
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {plan.name} ({lang_code}) - ${plan.price}'))
                    else:
                        updated_count += 1
                        self.stdout.write(f'  ↻ Updated: {plan.name} ({lang_code})')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Complete! Created {created_count}, Updated {updated_count} plans (EN + FR)\n'
        ))
