from django.utils import timezone
from django.db.models import Count, Sum, Avg, F, Q
from datetime import timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def _format_number(n):
    """Format large numbers with commas (e.g., 15650 -> '15,650')."""
    if isinstance(n, float):
        return f"{n:,.2f}"
    return f"{n:,}"


def _format_currency(amount):
    """Format as dollar currency (e.g., 1550.50 -> '$1,550.50')."""
    if amount is None:
        amount = 0
    if isinstance(amount, Decimal):
        amount = float(amount)
    if amount >= 1000:
        return f"${amount / 1000:,.1f}K"
    return f"${amount:,.2f}"


def _safe_percentage(part, total):
    """Calculate percentage safely, avoiding division by zero."""
    if total and total > 0:
        return round(part / total * 100, 1)
    return 0


def _get_monthly_labels(months=7):
    """Generate month labels for charts going back N months."""
    now = timezone.now()
    labels = []
    for i in range(months - 1, -1, -1):
        dt = now - timedelta(days=30 * i)
        labels.append(dt.strftime("%b"))
    return labels


def _get_monthly_data(queryset, months=7, date_field='created_at'):
    """Get monthly counts for the last N months from a queryset."""
    now = timezone.now()
    data = []
    for i in range(months - 1, -1, -1):
        end = now - timedelta(days=30 * i)
        start = end - timedelta(days=30)
        count = queryset.filter(
            **{f'{date_field}__gte': start, f'{date_field}__lt': end}
        ).count()
        data.append(count)
    return data


def _get_monthly_revenue_data(months=7):
    """Get monthly revenue data for the last N months."""
    from apps.payment.models import InAppPurchase

    now = timezone.now()
    monthly_data = []
    cumulative = 0
    cumulative_data = []

    for i in range(months - 1, -1, -1):
        end = now - timedelta(days=30 * i)
        start = end - timedelta(days=30)
        rev = InAppPurchase.objects.filter(
            status='verified',
            created_at__gte=start,
            created_at__lt=end
        ).aggregate(total=Sum('plan__price'))['total'] or 0
        rev = float(rev)
        monthly_data.append(round(rev, 2))
        cumulative += rev
        cumulative_data.append(round(cumulative, 2))

    return monthly_data, cumulative_data


def _get_monthly_ai_data(months=7):
    """Get monthly AI call counts and estimated costs."""
    from apps.watchanalysis.models import WatchAnalysis

    cost_per_call = 0.01
    now = timezone.now()
    calls_data = []
    cost_data = []

    for i in range(months - 1, -1, -1):
        end = now - timedelta(days=30 * i)
        start = end - timedelta(days=30)
        calls = WatchAnalysis.objects.filter(
            created_at__gte=start,
            created_at__lt=end
        ).count()
        calls_data.append(calls)
        cost_data.append(round(calls * cost_per_call, 2))

    return calls_data, cost_data


def dashboard_callback(request, context):
    """
    Unfold admin dashboard callback.
    Pulls real data from User, WatchAnalysis, InAppPurchase, and Subscription models.
    """
    from apps.user.models import User
    from apps.watchanalysis.models import WatchAnalysis
    from apps.payment.models import InAppPurchase
    from apps.subscription.models import Subscription

    now = timezone.now()
    today = now.date()
    thirty_days_ago = now - timedelta(days=30)
    twenty_four_hours_ago = now - timedelta(hours=24)

    # ─────────────────────────────────────────────────────────────
    # USER METRICS
    # ─────────────────────────────────────────────────────────────
    total_users = User.objects.count()
    free_users = User.objects.filter(subscription_type="free").count()
    premium_users = User.objects.filter(is_premium=True).count()
    active_users_daily = User.objects.filter(last_login__gte=twenty_four_hours_ago).count()
    active_users_monthly = User.objects.filter(last_login__gte=thirty_days_ago).count()

    # User growth (comparing last 30 days vs previous 30 days)
    sixty_days_ago = now - timedelta(days=60)
    users_last_30 = User.objects.filter(created_at__gte=thirty_days_ago).count()
    users_prev_30 = User.objects.filter(
        created_at__gte=sixty_days_ago,
        created_at__lt=thirty_days_ago
    ).count()
    user_growth_pct = _safe_percentage(users_last_30 - users_prev_30, users_prev_30) if users_prev_30 > 0 else 0

    conversion_rate = _safe_percentage(premium_users, total_users)

    # Premium ratio change (current premium % vs previous month's premium %)
    prev_premium = User.objects.filter(
        is_premium=True, created_at__lt=thirty_days_ago
    ).count()
    prev_total = User.objects.filter(created_at__lt=thirty_days_ago).count()
    prev_premium_pct = _safe_percentage(prev_premium, prev_total)
    current_premium_pct = _safe_percentage(premium_users, total_users)
    premium_change = round(current_premium_pct - prev_premium_pct, 1)

    # Active subscriptions
    active_subscriptions = Subscription.objects.filter(status='active').count()

    # Subscription churn (expired in last 30 days / total active)
    expired_last_30 = Subscription.objects.filter(
        status='expired',
        updated_at__gte=thirty_days_ago
    ).count()
    total_active_subs = active_subscriptions + expired_last_30
    subscription_churn = _safe_percentage(expired_last_30, total_active_subs)

    # User distribution percentages
    free_pct = _safe_percentage(free_users, total_users)
    premium_pct = _safe_percentage(premium_users, total_users)

    # ─────────────────────────────────────────────────────────────
    # ANALYSIS METRICS
    # ─────────────────────────────────────────────────────────────
    total_analyses = WatchAnalysis.objects.count()
    analyses_today = WatchAnalysis.objects.filter(created_at__date=today).count()
    analyses_this_month = WatchAnalysis.objects.filter(created_at__gte=thirty_days_ago).count()
    avg_analyses_per_user = round(total_analyses / total_users, 1) if total_users > 0 else 0

    # Average daily analyses (last 30 days)
    avg_daily_analyses = round(analyses_this_month / 30, 0) if analyses_this_month > 0 else 0

    # Free vs Premium analyses
    free_user_ids = User.objects.filter(is_premium=False).values_list('id', flat=True)
    free_analyses = WatchAnalysis.objects.filter(user_id__in=free_user_ids).count()
    premium_analyses = total_analyses - free_analyses

    # Monthly free vs premium analyses
    free_analyses_month = WatchAnalysis.objects.filter(
        user_id__in=free_user_ids,
        created_at__gte=thirty_days_ago
    ).count()
    premium_analyses_month = analyses_this_month - free_analyses_month

    # Analysis trends (last 11 months)
    analysis_labels = _get_monthly_labels(11)
    free_analysis_trend = _get_monthly_data(
        WatchAnalysis.objects.filter(user_id__in=free_user_ids), months=11
    )
    premium_analysis_trend = _get_monthly_data(
        WatchAnalysis.objects.exclude(user_id__in=free_user_ids), months=11
    )

    # ─────────────────────────────────────────────────────────────
    # REVENUE METRICS
    # ─────────────────────────────────────────────────────────────
    monthly_revenue = InAppPurchase.objects.filter(
        status='verified',
        created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('plan__price'))['total'] or Decimal('0')

    total_revenue = InAppPurchase.objects.filter(
        status='verified'
    ).aggregate(total=Sum('plan__price'))['total'] or Decimal('0')

    # MRR (Monthly Recurring Revenue from active subscriptions)
    mrr = InAppPurchase.objects.filter(
        status='verified',
        created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('plan__price'))['total'] or Decimal('0')

    # Average revenue per user
    avg_revenue_per_user = round(float(total_revenue) / total_users, 2) if total_users > 0 else 0

    # Revenue chart data (last 11 months)
    revenue_labels = _get_monthly_labels(11)
    monthly_rev_data, cumulative_rev_data = _get_monthly_revenue_data(months=11)

    # ─────────────────────────────────────────────────────────────
    # AI & COST MONITORING
    # ─────────────────────────────────────────────────────────────
    cost_per_call = 0.01
    ai_calls_monthly = WatchAnalysis.objects.filter(created_at__gte=thirty_days_ago).count()
    ai_cost_monthly = round(ai_calls_monthly * cost_per_call, 2)
    cost_per_analysis = round(cost_per_call, 4)
    ai_cost_pct_of_revenue = _safe_percentage(
        ai_cost_monthly, float(monthly_revenue)
    ) if float(monthly_revenue) > 0 else 0

    # AI cost chart data (last 7 months)
    ai_labels = _get_monthly_labels(7)
    ai_calls_data, ai_cost_data = _get_monthly_ai_data(months=7)

    # ─────────────────────────────────────────────────────────────
    # REPORTS METRICS
    # ─────────────────────────────────────────────────────────────
    # Reports by user type (last 7 months)
    reports_labels = _get_monthly_labels(7)
    free_reports_trend = _get_monthly_data(
        WatchAnalysis.objects.filter(user_id__in=free_user_ids), months=7
    )
    premium_reports_trend = _get_monthly_data(
        WatchAnalysis.objects.exclude(user_id__in=free_user_ids), months=7
    )

    # ─────────────────────────────────────────────────────────────
    # GEOGRAPHIC & CURRENCY
    # ─────────────────────────────────────────────────────────────
    # Currency distribution (USD vs EUR based on purchase platforms)
    usd_transactions = InAppPurchase.objects.filter(
        status='verified', platform='google'
    ).count()
    eur_transactions = InAppPurchase.objects.filter(
        status='verified', platform='apple'
    ).count()

    # ─────────────────────────────────────────────────────────────
    # SYSTEM HEALTH
    # ─────────────────────────────────────────────────────────────
    successful_analyses = WatchAnalysis.objects.filter(status='completed').count()
    failed_analyses = WatchAnalysis.objects.filter(status='failed').count()
    pending_analyses = WatchAnalysis.objects.filter(status='pending').count()
    success_rate = _safe_percentage(successful_analyses, total_analyses)
    error_rate = _safe_percentage(failed_analyses, total_analyses)

    system_status = 'Operational' if success_rate > 95 else 'Degraded' if success_rate > 80 else 'Critical'

    # Recent failed analyses for error logs
    recent_failures = WatchAnalysis.objects.filter(
        status='failed'
    ).select_related('user').order_by('-created_at')[:5]

    # ─────────────────────────────────────────────────────────────
    # RISK MONITORING & ALERTS
    # ─────────────────────────────────────────────────────────────
    alerts = []

    # AI cost alert
    ai_cost_alert = ai_cost_pct_of_revenue > 30
    if ai_cost_alert:
        alerts.append({
            'type': 'CRITICAL',
            'message': f'AI costs exceed 30% of total revenue [Current: {ai_cost_pct_of_revenue:.1f}%]',
        })

    # Analysis spike detection
    yesterday = today - timedelta(days=1)
    analyses_yesterday = WatchAnalysis.objects.filter(created_at__date=yesterday).count()
    if analyses_yesterday > 0 and analyses_today > 0:
        spike_pct = ((analyses_today - analyses_yesterday) / analyses_yesterday * 100)
        if spike_pct > 50:
            alerts.append({
                'type': 'WARNING',
                'message': f'Sudden spike in analysis volume detected – Current volume {spike_pct:.0f}% above normal',
            })

    # ═════════════════════════════════════════════════════════════
    # BUILD CONTEXT
    # ═════════════════════════════════════════════════════════════
    context.update({
        # --- User Metric Stat Cards ---
        "total_users": _format_number(total_users),
        "total_users_raw": total_users,
        "daily_active_users": _format_number(active_users_daily),
        "active_users": _format_number(active_users_monthly),
        "free_users": _format_number(free_users),
        "premium_users": premium_users,
        "premium_change": abs(premium_change),
        "premium_change_direction": "up" if premium_change >= 0 else "down",
        "conversion_rate": f"{conversion_rate}%",
        "user_growth": f"{user_growth_pct}%",
        "active_subscriptions": _format_number(active_subscriptions),
        "subscription_churn": f"{subscription_churn}%",

        # --- Analysis Stat Cards ---
        "total_analyses": _format_number(total_analyses),
        "daily_analyses": _format_number(analyses_today),
        "avg_daily_analyses": _format_number(int(avg_daily_analyses)),
        "analyses_this_month": _format_number(analyses_this_month),
        "avg_per_user": str(avg_analyses_per_user),
        "free_analyses": _format_number(free_analyses_month),
        "premium_analyses": _format_number(premium_analyses_month),

        # --- Revenue Stat Cards ---
        "monthly_revenue": _format_currency(float(monthly_revenue)),
        "total_revenue": _format_currency(float(total_revenue)),
        "total_revenue_stat": _format_currency(float(total_revenue)),
        "mrr": _format_currency(float(mrr)),
        "avg_revenue_per_user": f"${avg_revenue_per_user:.2f}",

        # --- AI & Cost Stat Cards ---
        "ai_calls_count": _format_number(ai_calls_monthly),
        "ai_cost_total": _format_currency(ai_cost_monthly),
        "cost_revenue_ratio": f"{ai_cost_pct_of_revenue:.1f}%",
        "ai_cost_stats": {
            "total_cost": _format_currency(ai_cost_monthly),
            "cost_per_analysis": f"${cost_per_analysis:.4f}",
            "monthly_trend": f"{ai_cost_pct_of_revenue:.1f}%",
        },

        # --- Geographic ---
        "markets_served": "N/A",
        "currency_split": f"{_format_number(usd_transactions)} / {_format_number(eur_transactions)}",
        "geographic_stats": {
            "users_usa": "N/A",
            "users_uk": "N/A",
            "users_germany": "N/A",
            "users_france": "N/A",
            "currency_usd": _format_number(usd_transactions),
            "currency_eur": _format_number(eur_transactions),
        },

        # --- System Health ---
        "system_health": {
            "api_uptime": {
                "label": "API Uptime",
                "value": f"{success_rate}%",
                "status": "green" if success_rate > 95 else "yellow",
            },
            "database_health": {
                "label": "Database Health",
                "value": system_status,
                "status": "green" if system_status == 'Operational' else "yellow",
            },
            "cache_hit_rate": {
                "label": "Success Rate",
                "value": f"{success_rate}%",
                "status": "green" if success_rate > 90 else "yellow",
            },
            "error_rate": {
                "label": "Error Rate",
                "value": f"{error_rate}%",
                "status": "green" if error_rate < 5 else "yellow" if error_rate < 15 else "red",
            },
        },

        # --- Recent Errors ---
        "recent_errors": recent_failures,

        # --- Alerts ---
        "alerts": alerts,

        # ═══════════════════════════════════════════════════════════
        # CHART DATA
        # ═══════════════════════════════════════════════════════════

        # --- Chart 1a: User Distribution (Doughnut) ---
        "user_distribution": {
            "labels": ["Free Users", "Premium Users"],
            "data": [free_users, premium_users],
            "percentages": [free_pct, premium_pct],
        },

        # --- Chart 1b: Reports by Type (Doughnut) ---
        "reports_by_type": {
            "labels": ["Premium Reports", "Free Reports"],
            "data": [premium_analyses, free_analyses],
        },

        # --- Chart 1c: Users by Country (Pie) ---
        # Note: User model doesn't have country field, showing subscription type distribution instead
        "users_by_country": {
            "labels": [
                "Free",
                "Pay-per-Scan",
                "Premium",
                "Unlimited",
                "Other"
            ],
            "data": [
                User.objects.filter(subscription_type='free').count(),
                User.objects.filter(subscription_type='pay_per_scan').count(),
                User.objects.filter(subscription_type='premium').count(),
                User.objects.filter(subscription_type='unlimited').count(),
                0,
            ],
        },

        # --- Chart 2: Analysis Trends (Line) ---
        "analysis_trends": {
            "labels": analysis_labels,
            "datasets": [
                {
                    "label": "Free Analyses",
                    "data": free_analysis_trend,
                },
                {
                    "label": "Premium Analyses",
                    "data": premium_analysis_trend,
                }
            ]
        },

        # --- Chart 3: Revenue Overview (Dual Axis Line) ---
        "revenue_overview": {
            "labels": revenue_labels,
            "datasets": [
                {
                    "label": "Revenue ($)",
                    "data": monthly_rev_data,
                },
                {
                    "label": "Transactions",
                    "data": cumulative_rev_data,
                    "yAxisID": "y2"
                }
            ]
        },

        # --- Chart 4: AI Cost Trends (Bar) ---
        "ai_cost": {
            "labels": ai_labels,
            "datasets": [
                {
                    "label": "AI Cost ($)",
                    "data": ai_cost_data,
                },
                {
                    "label": "% of Revenue",
                    "data": [
                        round(_safe_percentage(c, r), 1) if r > 0 else 0
                        for c, r in zip(
                            ai_cost_data,
                            _get_monthly_revenue_data(months=7)[0]
                        )
                    ],
                    "yAxisID": "y2"
                }
            ]
        },

        # --- Chart 5: Reports by User Type (Bar) ---
        "reports_user_type": {
            "labels": reports_labels,
            "datasets": [
                {
                    "label": "Free Users Reports",
                    "data": free_reports_trend,
                },
                {
                    "label": "Premium Users Reports",
                    "data": premium_reports_trend,
                }
            ]
        },

        # --- Chart 7: Currency Distribution (Bar) ---
        "currency_distribution": {
            "labels": ["Google Play (USD)", "App Store"],
            "data": [usd_transactions, eur_transactions]
        },
    })

    return context