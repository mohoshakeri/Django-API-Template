# AI-AGENT.md

This file provides guidance to AI-Agents when working with code in this repository.

---

## Commands

```bash
# Run all tests
python manage.py test

# Run a specific test module
python manage.py test tests.test_authentication

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver 0.0.0.0:3000
```

---

## Architecture Overview

### Directory Layout

- `apps/` — All Django apps. Every new app goes here.
- `services/` — Third-party integrations: Redis (`redis.py`), SMS (`sms.py`), Celery (`celery.py`).
- `tools/` — Pure Python utilities with no Django dependency: converters, datetime helpers, n-gram generators, JWT
  security, ...
- `utils/` — Django-aware utilities: base model/admin/view/test classes, permissions, session, validators,
  middlewares, ....
- `project_title/` — Django project: settings (base/development/production), root URLs, logging setup (`log.py`).
- `manager/` — Internal admin management app (logs, wallet requests, Redis flush command, ...).
- `CONSTANTS.py` — All magic numbers, strings, time values, and cache key prefixes, ... for the entire project.

### Mandatory Coding Checklist

Every time you write or modify code, you **must** complete all applicable items below — without being asked:

#### After Writing or Modifying Any View

- [ ] Apply Early Return pattern — no nested `if/else`, guard clauses at the top
- [ ] Add `logger.info` / `logger.warning` for every meaningful event (login, register, logout, state change, failure)
- [ ] Write or update the corresponding test class in `tests/test_<app>.py`

#### After Adding Any `_()` String

- [ ] Run `python manage.py makemessages -l fa --no-wrap`
- [ ] Open `locale/fa/LC_MESSAGES/django.po` and fill in the Persian `msgstr` for every new `msgid`
- [ ] Run `python manage.py compilemessages -l fa`

#### After Modifying Any Model

- [ ] Run `python manage.py makemigrations`

These are non-negotiable. Never skip them, never wait to be reminded.

---

### Coding Rules

#### Comments

Write comments in English, concise, only where necessary or to separate logical steps. Format: `# Capital Words Case`.

#### Docstrings

No docstrings anywhere **except** in view classes, only to describe supported HTTP methods:

```python
"""
GET -> Get User Info
POST -> Login Or Register
"""
```

#### Security Principle — Zero-Trust Access

**Core rule:** Default is deny. Access must be explicitly granted. Nothing is trusted, nothing is exposed unless
declared.

**Mental model:**

```
Nothing is trusted.
Nothing is exposed by default.
Access must be explicitly granted.
```

**Allow-list (required):** Define only what is permitted. Any new field or permission must be consciously added.

**Block-list (forbidden):** Never design security by removing unwanted items from an open set. Adding a new field to a
model must not silently expose it.

**Serializers — always use `fields`, never `exclude`:**

```python
# Correct: only declared fields are exposed
class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields: list[str] = ["id", "username", "email"]


# Wrong: a new model field will leak automatically
class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        exclude: list[str] = ["password"]  # Never do this
```

**Permissions & access control:**

- Grant the minimum required permission level.
- Never start with full access and then restrict.
- Never assume a user is trusted — authentication must be verified on every protected endpoint.

**Data exposure:**

- Only return data the API endpoint actually needs.
- Internal, system, and security fields must never be returned by default.
- Sensitive fields (tokens, hashed passwords, encryption keys) are never exposed.

**Checklist before writing any serializer, view, or permission:**

- Are all exposed fields explicitly declared?
- Does adding a new model field accidentally expose it?
- Is the minimum permission level enforced?
- Is any sensitive or internal data reachable through this endpoint?

#### Type Annotations

All variables, attributes, function parameters, and return types must have explicit type annotations.

#### Views

Business logic in views must delegate to model methods and standalone functions — not inline logic.

#### Property Methods

Properties that can be annotated must check for annotation first:

```python
@property
def items_count(self) -> int:
    if hasattr(self, "_items_count"):
        return self._items_count
    return self.items.count()
```

Use `annotate(_items_count=...)` with leading underscore in querysets.

#### View Conditionals — Early Return Pattern

Avoid `if/else` blocks in views. Use Early returns to keep code clean :

```python
# Wrong
def get(self, request):
    user = User.objects.filter(id=request.user.id).first()
    if user:
        return Response({"name": user.name}, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)


# Correct
def get(self, request):
    user = User.objects.filter(id=request.user.id).first()
    if not user:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response({"name": user.name}, status=status.HTTP_200_OK)
```

#### Object Retrieval — `get_object_or_error`

Never use Django's `get_object_or_404`. Use `get_object_or_error` from `utils.views` instead, which integrates with
`BaseView`'s error handling and returns structured JSON:

```python
# Wrong
from django.shortcuts import get_object_or_404

order = get_object_or_404(Order, id=id, is_finished=True)

# Correct
from utils.views import get_object_or_error

order = get_object_or_error(status_code=status.HTTP_400_BAD_REQUEST, message="Finished Order not founded.", Order,
                            id=id, is_finished=True)
```

#### Response Status Codes — DRF `status` Module

Always use named constants from `rest_framework.response` and `rest_framework import status`. Never use raw integers:

```python
# Wrong
return Response({"token": token}, status=200)
return Response(status=404)

# Correct
from rest_framework import status
from rest_framework.response import Response

return Response({"token": token}, status=status.HTTP_200_OK)
return Response(status=status.HTTP_404_NOT_FOUND)
```

#### String Formatting — `.format()` over f-strings

Use `"{}".format(...)` instead of f-strings throughout the codebase:

```python
# Wrong
message = f"Welcome {user.name}, your code is {code}"
cache_key = f"{VERIFICATION_CODE_CACHE_PREFIX}{mobile}"

# Correct
message = "Welcome {}, your code is {}".format(user.name, code)
cache_key = "{}{}".format(VERIFICATION_CODE_CACHE_PREFIX, mobile)
```

#### Model Choice Fields — Integer Steps of Ten

Never use strings as choice values. Use integers in steps of ten so future statuses can be inserted between existing
ones without breaking the sequence:

```python
# Wrong — strings and sequential integers leave no room for insertion
STATUS_CHOICES = (
    ("created", "Created"),
    ("pending", "Pending"),
    ("paid", "Paid"),
)

# Wrong — sequential integers: inserting between 1 and 2 is impossible
STATUS_CHOICES = (
    (1, _("Created")),
    (2, _("Pending")),
    (3, _("Paid")),
)

# Correct — tens leave room for future values between any two steps
PAYMENT_BILL_STATUSES: tuple[tuple[int, str], ...] = (
    (10, _("Created")),
    (20, _("Pending")),
    (30, _("Paid")),
)

# Later, inserting between 10 and 20 is clean:
PAYMENT_BILL_STATUSES: tuple[tuple[int, str], ...] = (
    (10, _("Created")),
    (15, _("Processing")),
    (20, _("Pending")),
    (30, _("Paid")),
)
```

Define choice tuples in `CONSTANTS.py` and import from there.

#### Language — English Source, Persian UI

All source code — variable names, comments, log messages, dev errors — must be in English. Persian is only for strings
that are shown directly to the end user.

Admin panel labels require Django's translation system because admin strings live in source code but are displayed in
Persian:

If you used _. you need to prepare it for translation. **ALWAYS**

```python
# CONSTANTS.py
from django.utils.translation import gettext_lazy as _

PAYMENT_BILL_STATUSES: tuple[tuple[int, str], ...] = (
    (10, _("Created")),
    (15, _("Processing")),
    (20, _("Pending")),
    (30, _("Paid")),
)

# models.py
from django.utils.translation import gettext_lazy as _
from CONSTANTS import PAYMENT_BILL_STATUSES


class Order(AbstractModel):
    status: int = models.IntegerField(
        choices=PAYMENT_BILL_STATUSES,
        verbose_name=_("Status"),
    )

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
```

```python
# admin.py
from django.utils.translation import gettext_lazy as _


class OrderAdmin(AbstractAdmin):
    ...
    # Column headers, filter labels, action names all use _()
```

Translation workflow:

```bash
# Extract strings marked with _() into .po files
python manage.py makemessages -l fa

# Edit locale/fa/LC_MESSAGES/django.po to provide Persian translations

# Compile .po → .mo (binary used at runtime)
python manage.py compilemessages
```

Rules:

- Use `gettext_lazy as _` (lazy version) in models, serializers, and admin — never the eager `gettext`.
- Use `gettext` (eager) only inside functions/methods that run at request time.
- Never write Persian strings directly in `verbose_name`, `help_text`, or admin labels — always wrap with `_()`.
- Plain user-facing response messages (returned in JSON) do **not** use the translation system — they are written
  directly in Persian in the view/serializer.

#### Response Messages — User vs Developer

Every error response has two distinct message roles. Never mix them.

**`message`** — Persian string for the end user. Shown directly in the UI. Must be human-friendly and free of technical
detail:

```python
{"message": "کد تایید اشتباه است"}
```

**`devMessage`** — English string (or `devMessages` for a list) for the developer. Contains technical context, field
names, validation detail. Never shown to the user:

```python
{"devMessage": "Verification code mismatch for mobile 09123456789"}
{"devMessages": ["code: must be 5 digits", "mobile: required"]}
```

**Decision rule — which key to use:**

| Situation                                                       | Key          | Reason                                                    |
|-----------------------------------------------------------------|--------------|-----------------------------------------------------------|
| Error the client should have caught (format, required field)    | `devMessage` | Client-side validation failed; user should never see this |
| Error only detectable server-side (wrong code, expired token)   | `message`    | Legitimate user-facing error                              |
| Serializer / validation detail                                  | `devMessage` | Internal, not meaningful to user                          |
| Business logic rejection (insufficient balance, locked account) | `message`    | User needs to know and act                                |

**Status code rules:**

- `2xx` — no message field needed.
- `5xx` — no message field; server errors must not leak internals.
- `4xx` — include `message` and/or `devMessage` as appropriate.

```python
# Wrong — leaking serializer internals to user
return Response(
    {"message": serializer.errors},
    status=status.HTTP_400_BAD_REQUEST,
)

# Correct — separate concerns
return Response(
    {
        "message": "اطلاعات وارد شده صحیح نیست",
        "devMessages": serializer.errors,
    },
    status=status.HTTP_400_BAD_REQUEST,
)

# Correct — server-side check, user must know
return Response(
    {"message": "کد تایید اشتباه است"},
    status=status.HTTP_400_BAD_REQUEST,
)
```

#### Naming

- Views: `NameView` (e.g., `AuthView`)
- Serializers: `NameSerializer` (e.g., `AuthSerializer`)

#### Imports

Within an app, use `from .models import *` (with `__all__` defined in each file). Across apps, use explicit imports:
`from apps.authentication.models import User`.

#### Placement

- Django-independent logic → `tools/<module>.py`
- Django-dependent utilities → `utils/<module>.py`
- All constants and configurable values → `CONSTANTS.py`, imported from there.

---

### Base Classes

#### `AbstractModel` (`utils/db.py`)

All models inherit from this. Adds `id`, `created_at`, `updated_at` automatically.

#### `AbstractAdmin` (`utils/admin.py`)

All admin classes inherit from this. Provides:

- `select_related_fields` / `prefetch_related_fields` for query optimization
- Jalali date widgets
- Auto-generated `list_display` and `list_filter`
- Persian-aware search

#### `BaseView` (`utils/views.py`)

All API views inherit from this. Catches `HTTPError` and returns structured JSON responses.

#### `WebAppAPITestCase` + `APITestCasePack` (`utils/test.py`)

All view tests use `WebAppAPITestCase`. Test cases are declared as `APITestCasePack` instances with typed
`APITestCaseModel` entries (input, output, expected_code). Call `self.run_tests()` to execute.

---

### Logging

Use `logger_set` from `project_title.log`:

```python
from project_title.log import logger_set

logger = logger_set("authentication.serializer")
logger.info(msg={"message": "Verification Code", "code": code, "mobile": mobile})
```

The logger name should reflect `<app>.<module>`.

Where it is important to record a **footprint**, log it with the information.

---

### Session & Authentication

Sessions are Redis-backed (`utils/session.py`). Authentication uses `Bearer` tokens validated via
`TokenAuthentication` (`utils/permissions.py`). Sessions auto-refresh on each request.

---

### Redis & Encryption

`services/redis.py` exposes a global `redis_client` instance. All stored values are encrypted and compressed
automatically. Use typed methods: `set_string`, `get_json`, `set_int`, etc.

Custom encrypted DB fields in `utils/db.py`: `EncryptedField` (searchable via hash + n-grams), `EncryptedTextField`,
`EncryptedJSONField`, `EncryptedMarkdownField`.

---

### SMS Service

Use `services/sms.py`:

```python
sms = SMS.ready(sms_name="template_name", code=code)
msg_id, report = sms.send(mobile=mobile, user_for_make_report=user, receiver_name=name)
```

Templates live in `templates/sms/`. In development mode the SMS is stubbed.

---

### Testing Pattern

After writing or modifying any view, write or update its tests:

```python
from utils.test import WebAppAPITestCase, APITestCasePack, APITestCaseModel


class AuthViewTest(WebAppAPITestCase):
    base_url = "/api/v1/auth/"
    test_cases = [
        APITestCasePack(
            title="Login With Code",
            method="POST",
            auth_required=False,
            cases=[
                APITestCaseModel(
                    input={"mobile": "09123456789", "code": "12345"},
                    output={"token": ...},
                    expected_code=200,
                )
            ],
        )
    ]

    def setUp(self):
        self.base_setUp()

    def test_login(self):
        self.run_tests()
```

---

### Deployment

- Container entry: `entrypoint.sh` → runs migrations, collects static, starts supervisord.
- Process manager: supervisord runs Gunicorn (`:3000`, 4 workers, 2 threads) + Nginx (`:80`).
- Deployment target: Liara (Iranian cloud), config in `liara.json`.
- Environment variables follow `.env.sample`.
