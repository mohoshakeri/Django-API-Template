import os

# Determine which settings to use based on DEPLOY environment variable
DEPLOY_STATUS = os.getenv("DEPLOY", "DEVELOPMENT")

if DEPLOY_STATUS == "PRODUCTION":
    from .production import *
else:
    from .development import *
