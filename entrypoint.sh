#!/usr/bin/env bash

# Create Logs Directories
mkdir -p /var/log/project_title/{nginx,supervisor,django}
mkdir -p /var/log/project_title/nginx/tmp/{body,proxy,fastcgi,uwsgi,scgi}

# Run Migrations
python manage.py migrate --skip-checks

# Restart Celery Beat
python manage.py shell <<EOF
from django_celery_beat.models import PeriodicTask

PeriodicTask.objects.update(enabled=False)
PeriodicTask.objects.update(last_run_at=None)
PeriodicTask.objects.update(enabled=True)

print("Celery Beat Reset Done")
EOF

# Execute Passed Command
exec "$@"
