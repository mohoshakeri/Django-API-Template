import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_title.settings")

# Import IS_PRODUCTION after setting DJANGO_SETTINGS_MODULE
from project_title.settings import IS_PRODUCTION

application = get_wsgi_application()

if IS_PRODUCTION:
    # For load static files in hosts
    from dj_static import Cling

    application = Cling(get_wsgi_application())
