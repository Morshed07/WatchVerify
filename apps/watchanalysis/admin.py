from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin
# Register your models here.

@admin.register(WatchAnalysis)
class WatchAnalysisAdmin(ModelAdmin):
    pass
@admin.register(UsageLog)
class UsageLogAdmin(ModelAdmin):
    pass