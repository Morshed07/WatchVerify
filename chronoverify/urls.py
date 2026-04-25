from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('apps.core.urls')),
    path('api/auth/', include('apps.user.urls')),
    path('api/subscription/', include('apps.subscription.urls')),
    path('api/payment/', include('apps.payment.urls')),
    path('api/watch-analysis/', include('apps.watchanalysis.urls')),




]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)