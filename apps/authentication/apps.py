from django.apps import AppConfig

from tools.converters import _


class authenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"
    label = "authentication"
    verbose_name = _("authentication")
