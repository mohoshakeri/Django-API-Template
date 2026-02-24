# Django REST Framework Template

## Local

- Replace all `project_title` with project name
- Replace `localhost:32` with `localhost:mn`
- Search for `domain_name.ir` and fix
- Run Migrations

## Production

- Fix `.env`
- Fix Disks and Volumes:

```json
[
  {
    "name": "storage",
    "mountTo": "/app/storage"
  },
  {
    "name": "static",
    "mountTo": "/app/static"
  },
  {
    "name": "assets",
    "mountTo": "/app/assets"
  },
  {
    "name": "logs",
    "mountTo": "/var/log/project_title"
  }
]
```
