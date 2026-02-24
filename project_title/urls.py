import os

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, register_converter
from django.views.generic import RedirectView
from project_title.settings import (
    ADMIN_PATH,
    CORE_BASE_URL,
    STATIC_URL,
    IS_PRODUCTION,
    BASE_DIR,
    ASSETS_URL,
    APP_BASE_URL,
)

from utils.converters import DatetimeConverter, BoolConverter, DateConverter
from .admin import movasa_admin_site

# Register custom URL path converters
register_converter(BoolConverter, "bool")
register_converter(DatetimeConverter, "datetime")
register_converter(DateConverter, "date")

# API configuration
VERSION_CODE: str = "v1"
API_PREFIX: str = f"api/{VERSION_CODE}"

urlpatterns = [
    path("", RedirectView.as_view(url=APP_BASE_URL)),
    # Admin panel endpoints
    path(f"{ADMIN_PATH}/", include("massadmin.urls")),
    path(f"{ADMIN_PATH}/", movasa_admin_site.urls),
    # API endpoints
    path(f"{API_PREFIX}/auth/", include("apps.authentication.urls")),
]

# Admin panel customization
admin.AdminSite.site_title = "project_title"
admin.AdminSite.site_header = "project_title"
admin.AdminSite.site_url = CORE_BASE_URL
admin.AdminSite.empty_value_display = "* * *"


if not IS_PRODUCTION:
    urlpatterns += static(STATIC_URL, document_root=os.path.join(BASE_DIR, "static"))
    urlpatterns += static(ASSETS_URL, document_root=os.path.join(BASE_DIR, "assets"))
