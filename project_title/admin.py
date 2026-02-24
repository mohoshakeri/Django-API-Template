from django.contrib import admin


class CustomAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        return super().index(request, extra_context)


movasa_admin_site = CustomAdminSite(name="admin")
movasa_admin_site._registry.update(admin.site._registry)
