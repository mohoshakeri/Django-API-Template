from django.contrib import admin

from utils.admin import AbstractAdmin
from .models import *


@admin.register(AdminActionLog)
class AdminActionLogAdmin(AbstractAdmin):
    search_fields = ("admin__pk", "admin__mobile", "string_details")
    display_fields: list[str] = [
        "id",
        "created_at",
        "updated_at",
        "admin",
        "string_details",
    ]


@admin.register(ChargeWalletRequest)
class ChargeWalletRequestAdmin(AbstractAdmin):
    search_fields = (
        "user__pk",
        "user__mobile",
        "user__name",
        "author__mobile",
    )
    display_fields: list[str] = [
        "id",
        "created_at",
        "updated_at",
        "is_successful",
        "description",
        "response",
        "docs",
        "user",
        "amount",
        "author",
    ]
    fields = ("user", "amount", "description", "docs")


@admin.register(WalletHistory)
class WalletHistoryAdmin(AbstractAdmin):
    search_fields = (
        "user__pk",
        "user__mobile",
        "user__name",
    )
    display_fields: list[str] = [
        "id",
        "created_at",
        "updated_at",
        "user",
        "before",
        "charge",
        "after",
        "description",
    ]
    fields = ("user", "before", "charge", "description")
