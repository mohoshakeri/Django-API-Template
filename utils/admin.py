from django.contrib import admin
from django.contrib.admin.utils import display_for_field as base_display_for_field
from django.db import models
from django.db.models import BooleanField, NullBooleanField
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget
from jalali_date_new.fields import JalaliDateTimeField, JalaliDateField
from jalali_date_new.widgets import (
    AdminJalaliDateTimeWidget,
    AdminJalaliDateWidget,
)
from massadmin.massadmin import mass_change_selected

from tools.converters import _
from tools.datetimes import jdt
from utils.db import search_by_query


def display_for_field(value, field, *args, **kwargs):
    if isinstance(field, models.DateTimeField) and value:
        return jdt.datetime.fromgregorian(datetime=value).strftime("%Y/%m/%d - %H:%M")
    if isinstance(field, models.DateField) and value:
        return jdt.datetime.fromgregorian(date=value).date().strftime("%Y/%m/%d")
    return base_display_for_field(value, field, *args, **kwargs)


admin.utils.display_for_field = display_for_field


class AbstractAdmin(admin.ModelAdmin):
    model = models.Model
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
        models.DateTimeField: {
            "form_class": JalaliDateTimeField,
            "widget": AdminJalaliDateTimeWidget,
        },
        models.DateField: {
            "form_class": JalaliDateField,
            "widget": AdminJalaliDateWidget,
        },
    }
    list_filter_classes = []
    display_fields: list[str] = []
    select_related_fields: list[str] = []
    prefetch_related_fields: list[str] = []
    raw_actions = []
    raw_actions_classes = {"delete_selected": "btn-error"}
    exclude_raw_actions = ["mass_change_selected"]
    list_per_page = 100
    ordering = ("-created_at", "-updated_at")
    date_hierarchy = "created_at"

    # 1. QUERYSETS

    def _queryset_handler(self, queryset):
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)

        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)

        return queryset

    def get_queryset(self, request):
        return self._queryset_handler(super().get_queryset(request))

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            q = search_by_query(search_fields=self.search_fields, query=search_term)
            queryset = self._queryset_handler(queryset.filter(q))

        return queryset.distinct(), False

    # 2. DISPLAYS

    def get_list_display(self, request):
        # Get All Property Names That Are Not Methods And Not Private
        property_fields: list[str] = [
            attr
            for attr in dir(self.model)
            if isinstance(getattr(self.model, attr), property)
            and not attr.startswith("_")
        ]

        if self.display_fields:
            # Explicit Allow-List Defined On The Admin Class
            fields_display: list[str] = list(self.display_fields)
        else:
            # Auto-Detect: All Model Fields + Properties
            model_fields: list[str] = [field.name for field in self.model._meta.fields]
            fields_display = model_fields + property_fields

        # Create Admin Method Wrappers For Properties That Appear In The Display List
        for prop in property_fields:
            if prop not in fields_display:
                continue

            prop_obj = getattr(self.model, prop)

            # Only Boolean Properties Get The Icon Treatment
            is_bool: bool = bool(
                prop_obj.fget and prop_obj.fget.__annotations__.get("return") is bool
            )

            # If Already Exists, No Need To Add Again
            if not hasattr(self.__class__, prop):

                def make_wrapper(prop_name: str, boolean: bool, description: str):
                    def wrapper(self, obj):
                        return getattr(obj, prop_name)

                    wrapper.boolean = boolean
                    wrapper.short_description = description
                    return wrapper

                # Prefer Short Description From Getter If Available
                description: str = getattr(
                    prop_obj.fget, "short_description", prop.replace("_", " ").title()
                )
                setattr(self.__class__, prop, make_wrapper(prop, is_bool, description))

        actions = super().get_actions(request)
        self.raw_actions = actions
        fields_display.insert(1, "action_raw_buttons")

        return fields_display

    def action_raw_buttons(self, obj):
        actions = self.raw_actions
        buttons = [
            '<button class="action-btn button btn btn-sm {}" type="button" data-action="{}" data-id="{}">{}</button>'.format(
                self.raw_actions_classes.get(action_name, "btn-primary"),
                action_name,
                obj.id,
                action_name.replace("selected", "").replace("_", " ").title(),
            )
            for action_name in actions.keys()
            if action_name not in self.exclude_raw_actions
        ]

        return format_html(" ".join(buttons))

    action_raw_buttons.short_description = _("Actions")

    def get_list_filter(self, request):
        # Start With Defined list_filter If Any
        defined_filters = list(self.list_filter) if hasattr(self, "list_filter") else []

        # Collect Fields Already Included
        defined_filter_names = set()
        for item in defined_filters:
            if isinstance(item, str):
                defined_filter_names.add(item)
            elif hasattr(item, "parameter_name"):
                defined_filter_names.add(item.parameter_name)

        # Get Fields From Model
        model_fields = self.model._meta.fields
        extra_filters = []

        for field in model_fields:
            if field.name in defined_filter_names:
                continue

            # Add Boolean Or NullBoolean Fields
            if isinstance(field, (BooleanField, NullBooleanField)):
                extra_filters.append(field.name)

            # Add Fields With Choices
            elif field.choices:
                extra_filters.append(field.name)

        # Combine And Return
        return defined_filters + extra_filters

    def get_list_display_links(self, request, list_display):
        if request.user.is_superuser:
            return self.list_display_links or ("id",)

        fields = self.get_fields(request)
        if fields:
            return self.list_display_links or ("id",)
        return None

    # 3. FORMS

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            # Superuser Sees All Concrete Model Fields
            fields: list[str] = [f.name for f in self.model._meta.fields] + [
                f.name for f in self.model._meta.many_to_many
            ]
        else:
            # Staff Sees Only The Fields Declared Via The Native Django `fields` Attribute
            fields = list(super().get_fields(request, obj))

        many_to_many_rels: list[str] = [
            field.name
            for field in self.model._meta.get_fields()
            if field.name in fields
            and isinstance(field, (models.ManyToManyField, models.ManyToManyRel))
        ]
        one_rels: list[str] = [
            field.name
            for field in self.model._meta.get_fields()
            if field.name in fields
            and isinstance(
                field,
                (
                    models.OneToOneRel,
                    models.ManyToOneRel,
                    models.OneToOneField,
                    models.ForeignKey,
                ),
            )
        ]
        self.raw_id_fields = one_rels
        self.autocomplete_fields = one_rels
        self.filter_horizontal = many_to_many_rels

        return fields

    # 4. ACTIONS
    def get_actions(self, request):
        if self.has_change_permission(request):
            self.actions = (mass_change_selected,) + self.actions

        return super().get_actions(request)

    def delete_queryset(self, request, queryset):
        # For distinct bug
        ids = list(queryset.values_list("pk", flat=True))
        clean_queryset = queryset.model.objects.filter(pk__in=ids)
        clean_queryset.delete()
