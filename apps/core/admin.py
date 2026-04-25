from django.contrib import admin
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from apps.user.models import User
# from apps.subscription.models import SubscriptionPlan
from apps.watchanalysis.models import WatchAnalysis
from apps.payment.models import InAppPurchase
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# USER ADMIN
# ============================================================================
# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ['email', 'first_name', 'subscription_type', 'is_premium', 'total_scans_used', 'created_at']
#     list_filter = ['subscription_type', 'is_premium', 'is_active', 'created_at']
#     search_fields = ['email', 'first_name', 'last_name']
#     readonly_fields = ['id', 'created_at', 'updated_at', 'total_scans_used']
    
#     fieldsets = (
#         ('Account Info', {
#             'fields': ('email', 'first_name', 'last_name', 'is_active')
#         }),
#         ('Subscription', {
#             'fields': ('subscription_type', 'is_premium', 'subscription_start_date', 'subscription_end_date')
#         }),
#         ('Usage', {
#             'fields': ('free_scans_remaining', 'total_scans_used')
#         }),
#         ('Payment', {
#             'fields': ('stripe_customer_id',)
#         }),
#         ('Timestamps', {
#             'fields': ('id', 'created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )


# # ============================================================================
# # WATCH ANALYSIS ADMIN
# # ============================================================================
# @admin.register(WatchAnalysis)
# class WatchAnalysisAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user_email', 'authenticity_level', 'confidence_score', 'status', 'created_at']
#     list_filter = ['status', 'authenticity_level', 'created_at']
#     search_fields = ['user__email', 'brand_detected', 'model_detected']
#     readonly_fields = ['id', 'created_at', 'updated_at', 'processing_time']
    
#     def user_email(self, obj):
#         return obj.user.email
#     user_email.short_description = 'User Email'
    
#     fieldsets = (
#         ('User & Status', {
#             'fields': ('user', 'status', 'created_at')
#         }),
#         ('Analysis Results', {
#             'fields': ('authenticity_level', 'confidence_score', 'brand_detected', 'model_detected')
#         }),
#         ('Images', {
#             'fields': ('front_image', 'back_image', 'bracelet_image')
#         }),
#         ('Details', {
#             'fields': ('estimated_price', 'processing_time', 'error_message'),
#             'classes': ('collapse',)
#         }),
#     )


# # ============================================================================
# # SUBSCRIPTION PLAN ADMIN
# # ============================================================================
# @admin.register(SubscriptionPlan)
# class SubscriptionPlanAdmin(admin.ModelAdmin):
#     list_display = ['name', 'category', 'price', 'duration_days', 'scans_included', 'is_active']
#     list_filter = ['category', 'is_active', 'analysis_type']
#     search_fields = ['name', 'description']
    
#     fieldsets = (
#         ('Basic Info', {
#             'fields': ('name', 'category', 'description', 'is_active')
#         }),
#         ('Pricing', {
#             'fields': ('price', 'duration_days', 'scans_included')
#         }),
#         ('Store IDs', {
#             'fields': ('google_product_id', 'apple_product_id')
#         }),
#         ('Analysis Features', {
#             'fields': ('analysis_type', 'basic_authenticity_check', 'fast_processing')
#         }),
#     )


# # ============================================================================
# # IN-APP PURCHASE ADMIN
# # ============================================================================
# @admin.register(InAppPurchase)
# class InAppPurchaseAdmin(admin.ModelAdmin):
#     list_display = ['user', 'plan', 'platform', 'status', 'purchase_date']
#     list_filter = ['status', 'platform', 'purchase_date']
#     search_fields = ['user__email', 'product_id']
#     readonly_fields = ['id', 'created_at', 'verified_at']
    
#     fieldsets = (
#         ('Basic Info', {
#             'fields': ('user', 'plan', 'platform', 'status')
#         }),
#         ('Purchase Details', {
#             'fields': ('product_id', 'purchase_date', 'expiry_date')
#         }),
#         ('Google Play', {
#             'fields': ('google_order_id', 'google_product_id', 'google_purchase_token'),
#             'classes': ('collapse',)
#         }),
#         ('Apple App Store', {
#             'fields': ('apple_transaction_id', 'apple_original_transaction_id', 'apple_product_id'),
#             'classes': ('collapse',)
#         }),
#         ('Verification', {
#             'fields': ('is_verified', 'verified_at'),
#             'classes': ('collapse',)
#         }),
#     )


# ============================================================================
# METRICS DASHBOARDS
# ============================================================================

class UserMetricsAdmin(admin.ModelAdmin):
    """User Metrics Dashboard"""
    change_list_template = 'admin/user_metrics.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Calculate user metrics
        total_users = User.objects.count()
        
        # Active users (monthly)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_users_monthly = User.objects.filter(updated_at__gte=thirty_days_ago).count()
        
        # Active users (daily)
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        active_users_daily = User.objects.filter(updated_at__gte=twenty_four_hours_ago).count()
        
        # Free vs Premium
        free_users = User.objects.filter(subscription_type='free').count()
        premium_users = User.objects.filter(is_premium=True).count()
        
        # Conversion rate
        conversion_rate = (premium_users / total_users * 100) if total_users > 0 else 0
        
        extra_context['metrics'] = {
            'total_users': total_users,
            'active_users_daily': active_users_daily,
            'active_users_monthly': active_users_monthly,
            'free_users': free_users,
            'premium_users': premium_users,
            'conversion_rate': f"{conversion_rate:.2f}%",
        }
        
        return super().changelist_view(request, extra_context=extra_context)


class AnalysisMetricsAdmin(admin.ModelAdmin):
    """Analysis Usage Metrics Dashboard"""
    change_list_template = 'admin/analysis_metrics.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Calculate analysis metrics
        total_analyses = WatchAnalysis.objects.count()
        
        # Analyses per day
        today = timezone.now().date()
        analyses_today = WatchAnalysis.objects.filter(created_at__date=today).count()
        
        # Analyses per month
        thirty_days_ago = timezone.now() - timedelta(days=30)
        analyses_monthly = WatchAnalysis.objects.filter(created_at__gte=thirty_days_ago).count()
        
        # Free vs Premium analyses
        free_user_ids = User.objects.filter(is_premium=False).values_list('id', flat=True)
        free_analyses = WatchAnalysis.objects.filter(user_id__in=free_user_ids).count()
        premium_analyses = total_analyses - free_analyses
        
        # Average analyses per user
        total_users = User.objects.count()
        avg_analyses = (total_analyses / total_users) if total_users > 0 else 0
        
        extra_context['metrics'] = {
            'total_analyses': total_analyses,
            'analyses_today': analyses_today,
            'analyses_monthly': analyses_monthly,
            'free_analyses': free_analyses,
            'premium_analyses': premium_analyses,
            'avg_analyses_per_user': f"{avg_analyses:.2f}",
        }
        
        return super().changelist_view(request, extra_context=extra_context)


class RevenueMetricsAdmin(admin.ModelAdmin):
    """Revenue Metrics Dashboard"""
    change_list_template = 'admin/revenue_metrics.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Calculate revenue metrics
        thirty_days_ago = timezone.now() - timedelta(days=30)
        monthly_revenue = InAppPurchase.objects.filter(
            status='verified',
            created_at__gte=thirty_days_ago
        ).aggregate(total=Sum('plan__price'))['total'] or 0
        
        # Total revenue
        total_revenue = InAppPurchase.objects.filter(
            status='verified'
        ).aggregate(total=Sum('plan__price'))['total'] or 0
        
        # Revenue by plan
        revenue_by_plan = (
            InAppPurchase.objects
            .filter(status='verified')
            .values('plan__name')
            .annotate(total=Sum('plan__price'), count=Count('id'))
            .order_by('-total')
        )
        
        extra_context['metrics'] = {
            'monthly_revenue': f"${monthly_revenue:.2f}",
            'total_revenue': f"${total_revenue:.2f}",
            'revenue_by_plan': list(revenue_by_plan),
        }
        
        return super().changelist_view(request, extra_context=extra_context)


class AIandCostMonitoringAdmin(admin.ModelAdmin):
    """AI & Cost Monitoring Dashboard"""
    change_list_template = 'admin/ai_cost_monitoring.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Calculate AI cost metrics
        today = timezone.now().date()
        ai_calls_today = WatchAnalysis.objects.filter(created_at__date=today).count()
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        ai_calls_monthly = WatchAnalysis.objects.filter(created_at__gte=thirty_days_ago).count()
        
        # Estimated AI cost (assuming $0.01 per API call)
        cost_per_call = 0.01
        estimated_daily_cost = ai_calls_today * cost_per_call
        estimated_monthly_cost = ai_calls_monthly * cost_per_call
        
        # AI cost as percentage of revenue
        monthly_revenue = InAppPurchase.objects.filter(
            status='verified',
            created_at__gte=thirty_days_ago
        ).aggregate(total=Sum('plan__price'))['total'] or 1  # Avoid division by zero
        
        ai_cost_percentage = (estimated_monthly_cost / monthly_revenue * 100) if monthly_revenue > 0 else 0
        
        # Risk alert for AI costs exceeding 30% of revenue
        ai_cost_alert = ai_cost_percentage > 30
        
        extra_context['metrics'] = {
            'ai_calls_today': ai_calls_today,
            'ai_calls_monthly': ai_calls_monthly,
            'estimated_daily_cost': f"${estimated_daily_cost:.2f}",
            'estimated_monthly_cost': f"${estimated_monthly_cost:.2f}",
            'ai_cost_percentage': f"{ai_cost_percentage:.2f}%",
            'ai_cost_alert': ai_cost_alert,
            'alert_message': 'WARNING: AI costs exceed 30% of revenue!' if ai_cost_alert else 'AI costs within normal range',
        }
        
        return super().changelist_view(request, extra_context=extra_context)


class ReportsMetricsAdmin(admin.ModelAdmin):
    """Reports Metrics Dashboard"""
    change_list_template = 'admin/reports_metrics.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Total reports generated (assuming each analysis = 1 report)
        total_reports = WatchAnalysis.objects.count()
        
        # Reports by free vs premium users
        free_user_ids = User.objects.filter(is_premium=False).values_list('id', flat=True)
        reports_free_users = WatchAnalysis.objects.filter(user_id__in=free_user_ids).count()
        reports_premium_users = total_reports - reports_free_users
        
        extra_context['metrics'] = {
            'total_reports': total_reports,
            'reports_free_users': reports_free_users,
            'reports_premium_users': reports_premium_users,
            'free_percentage': f"{(reports_free_users / total_reports * 100) if total_reports > 0 else 0:.2f}%",
            'premium_percentage': f"{(reports_premium_users / total_reports * 100) if total_reports > 0 else 0:.2f}%",
        }
        
        return super().changelist_view(request, extra_context=extra_context)


class GeographicCurrencyDataAdmin(admin.ModelAdmin):
    """Geographic & Currency Data Dashboard"""
    change_list_template = 'admin/geographic_currency.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # User distribution (by country if country field exists)
        # Placeholder - update based on your User model fields
        total_users = User.objects.count()
        
        # Currency usage (USD vs EUR) - placeholder
        # This would depend on your payment/subscription tracking
        usd_revenue = InAppPurchase.objects.filter(
            status='verified'
        ).aggregate(total=Sum('plan__price'))['total'] or 0
        
        extra_context['metrics'] = {
            'total_users': total_users,
            'note': 'Geographic and currency data tracking requires additional user profile fields (country, preferred_currency)',
            'usd_revenue': f"${usd_revenue:.2f}",
            'eur_revenue': '$0.00',  # Placeholder
        }
        
        return super().changelist_view(request, extra_context=extra_context)


class SystemOverviewAdmin(admin.ModelAdmin):
    """System Overview Dashboard"""
    change_list_template = 'admin/system_overview.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # System health indicators
        total_analyses = WatchAnalysis.objects.count()
        successful_analyses = WatchAnalysis.objects.filter(status='completed').count()
        failed_analyses = WatchAnalysis.objects.filter(status='failed').count()
        pending_analyses = WatchAnalysis.objects.filter(status='pending').count()
        
        success_rate = (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0
        error_rate = (failed_analyses / total_analyses * 100) if total_analyses > 0 else 0
        
        # Get error logs
        # This is a placeholder - adjust based on your logging setup
        recent_errors = []
        try:
            # You can expand this to query actual error logs from a model if you have one
            recent_errors = []
        except Exception as e:
            logger.error(f"Error fetching error logs: {str(e)}")
        
        extra_context['metrics'] = {
            'total_analyses': total_analyses,
            'successful_analyses': successful_analyses,
            'failed_analyses': failed_analyses,
            'pending_analyses': pending_analyses,
            'success_rate': f"{success_rate:.2f}%",
            'error_rate_value': f"{error_rate:.2f}",
            'error_rate': f"{error_rate:.2f}%",
            'error_rate_numeric': error_rate,
            'system_status': 'Operational' if success_rate > 95 else 'Degraded' if success_rate > 80 else 'Critical',
            'recent_errors': recent_errors,
        }
        
        return super().changelist_view(request, extra_context=extra_context)


class RiskMonitoringAlertsAdmin(admin.ModelAdmin):
    """Visual Alerts & Risk Monitoring Dashboard"""
    change_list_template = 'admin/risk_monitoring.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        alerts = []
        
        # Alert 1: AI costs exceed 30% of total revenue
        thirty_days_ago = timezone.now() - timedelta(days=30)
        ai_calls_monthly = WatchAnalysis.objects.filter(created_at__gte=thirty_days_ago).count()
        cost_per_call = 0.01
        estimated_monthly_cost = ai_calls_monthly * cost_per_call
        
        monthly_revenue = InAppPurchase.objects.filter(
            status='verified',
            created_at__gte=thirty_days_ago
        ).aggregate(total=Sum('plan__price'))['total'] or 1
        
        ai_cost_percentage = (estimated_monthly_cost / monthly_revenue * 100) if monthly_revenue > 0 else 0
        
        if ai_cost_percentage > 30:
            alerts.append({
                'type': 'CRITICAL',
                'message': f'AI costs exceed 30% of total revenue ({ai_cost_percentage:.2f}%)',
                'value': f"${estimated_monthly_cost:.2f} / ${monthly_revenue:.2f}",
            })
        
        # Alert 2: Premium conversion rate falls below 2%
        total_users = User.objects.count()
        premium_users = User.objects.filter(is_premium=True).count()
        conversion_rate = (premium_users / total_users * 100) if total_users > 0 else 0
        
        if conversion_rate < 2:
            alerts.append({
                'type': 'WARNING',
                'message': f'Premium conversion rate is below 2% ({conversion_rate:.2f}%)',
                'value': f"{premium_users} / {total_users} users",
            })
        
        # Alert 3: User exceeds abnormal analysis threshold
        # Define abnormal threshold as more than 100 analyses per user
        abnormal_threshold = 100
        top_users = User.objects.annotate(
            analysis_count=Count('analyses')
        ).filter(analysis_count__gt=abnormal_threshold).values('email', 'analysis_count')
        
        for user in top_users:
            alerts.append({
                'type': 'INFO',
                'message': f'User exceeds abnormal analysis threshold',
                'value': f"{user['email']}: {user['analysis_count']} analyses",
            })
        
        # Alert 4: Sudden spike in analysis volume
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        analyses_today = WatchAnalysis.objects.filter(created_at__date=today).count()
        analyses_yesterday = WatchAnalysis.objects.filter(created_at__date=yesterday).count()
        
        # Define spike as 50% increase
        if analyses_yesterday > 0 and (analyses_today / analyses_yesterday) > 1.5:
            spike_percentage = ((analyses_today - analyses_yesterday) / analyses_yesterday * 100)
            alerts.append({
                'type': 'WARNING',
                'message': f'Sudden spike in analysis volume detected',
                'value': f"Today: {analyses_today} | Yesterday: {analyses_yesterday} ({spike_percentage:.2f}% increase)",
            })
        
        extra_context['alerts'] = {
            'total_alerts': len(alerts),
            'critical_alerts': sum(1 for a in alerts if a['type'] == 'CRITICAL'),
            'warning_alerts': sum(1 for a in alerts if a['type'] == 'WARNING'),
            'info_alerts': sum(1 for a in alerts if a['type'] == 'INFO'),
            'alerts': alerts,
            'conversion_rate': f"{conversion_rate:.2f}%",
            'ai_cost_percentage': f"{ai_cost_percentage:.2f}%",
        }
        
        return super().changelist_view(request, extra_context=extra_context)


# Create proxy models for metrics views
class UserMetricsProxy(User):
    class Meta:
        proxy = True
        verbose_name_plural = "User Metrics"


class AnalysisMetricsProxy(WatchAnalysis):
    class Meta:
        proxy = True
        verbose_name_plural = "Analysis Metrics"


class RevenueMetricsProxy(InAppPurchase):
    class Meta:
        proxy = True
        verbose_name_plural = "Revenue Metrics"


class AIandCostMonitoringProxy(WatchAnalysis):
    class Meta:
        proxy = True
        verbose_name = "AI & Cost Monitoring"
        verbose_name_plural = "AI & Cost Monitoring"


class ReportsMetricsProxy(WatchAnalysis):
    class Meta:
        proxy = True
        verbose_name = "Reports Metrics"
        verbose_name_plural = "Reports Metrics"


class GeographicCurrencyProxy(User):
    class Meta:
        proxy = True
        verbose_name = "Geographic & Currency Data"
        verbose_name_plural = "Geographic & Currency Data"


class SystemOverviewProxy(WatchAnalysis):
    class Meta:
        proxy = True
        verbose_name = "System Overview"
        verbose_name_plural = "System Overview"


class RiskMonitoringProxy(User):
    class Meta:
        proxy = True
        verbose_name = "Risk Monitoring & Alerts"
        verbose_name_plural = "Risk Monitoring & Alerts"


# Register metrics dashboards
admin.site.register(UserMetricsProxy, UserMetricsAdmin)
admin.site.register(AnalysisMetricsProxy, AnalysisMetricsAdmin)
admin.site.register(RevenueMetricsProxy, RevenueMetricsAdmin)
admin.site.register(AIandCostMonitoringProxy, AIandCostMonitoringAdmin)
admin.site.register(ReportsMetricsProxy, ReportsMetricsAdmin)
admin.site.register(GeographicCurrencyProxy, GeographicCurrencyDataAdmin)
admin.site.register(SystemOverviewProxy, SystemOverviewAdmin)
admin.site.register(RiskMonitoringProxy, RiskMonitoringAlertsAdmin)


