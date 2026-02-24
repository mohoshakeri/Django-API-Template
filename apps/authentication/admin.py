from django.contrib import admin
from django.contrib.auth.models import Group
from django_celery_results.models import GroupResult

from tools.converters import _
from utils.admin import AbstractAdmin
from .models import *

admin.site.unregister(Group)
admin.site.unregister(GroupResult)


@admin.register(User)
class UserAdmin(AbstractAdmin):
    def get_list_display(self, request):
        return self.list_display

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return self._queryset_handler(
            super().get_queryset(request).filter(is_superuser=False, is_staff=False)
        )

    fieldsets = (
        (None, {"fields": ("mobile", "password")}),
        (_("Personal Info"), {"fields": ("name", "address")}),
        (_("Finance Info"), {"fields": ("wallet",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("mobile", "usable_password", "password1", "password2"),
            },
        ),
    )

    list_display = (
        "created_at",
        "updated_at",
        "id",
        "mobile",
        "name",
        "address",
        "wallet",
        "is_superuser",
        "is_staff",
        "last_login",
    )
    list_display_links = ("mobile",)
    search_fields = ("pk", "name", "mobile", "address")

    ordering = ("-created_at",)
    date_hierarchy = None
