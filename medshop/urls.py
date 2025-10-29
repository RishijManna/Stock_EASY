from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # App routes
    path("", include(("inventory.urls", "inventory"), namespace="inventory")),
    path("reports/", include(("reports.urls", "reports"), namespace="reports")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),  # <-- namespace it
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
