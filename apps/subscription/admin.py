from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import SubscriptionPlan, Subscription
# Register your models here.

admin.site.register(SubscriptionPlan, ModelAdmin)
admin.site.register(Subscription, ModelAdmin)
