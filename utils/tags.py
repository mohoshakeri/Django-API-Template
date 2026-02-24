from django import template
from project_title.settings import CORE_BASE_URL, STATIC_URL, ASSETS_URL, MEDIA_URL

from tools.converters import md_to_html, number_to_string, add_thousand_separator
from tools.datetimes import dt_to_text

register = template.Library()
DEFAULT = "***"


@register.filter
def add(int1, int2):
    return int1 + int2


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_item_or_zero(dictionary, key) -> int:
    item = dictionary.get(key)
    if item is not None:
        return item
    return 0


@register.filter
def get_index(list, index):
    return list[index - 1]


@register.filter
def standard_datetime(datetime, default=DEFAULT):
    if datetime:
        return dt_to_text(datetime)
    return default


@register.filter
def standard_date(datetime, default=DEFAULT):
    if datetime:
        return dt_to_text(datetime, time_check=False)
    return default


@register.filter
def datetime_diff(datetime2, datetime1):
    return (datetime2 - datetime1).days // 365


@register.filter
def en_datetime(datetime, default=DEFAULT):
    if datetime:
        return dt_to_text(datetime, lang="English")
    return default


@register.filter
def md_to_html(content, default=DEFAULT):
    if content:
        return md_to_html(content)
    return default


@register.filter
def to_string(content, default=DEFAULT):
    if content:
        return number_to_string(content)
    return default


@register.filter
def to_iso_number(number, default=DEFAULT):
    if number:
        return add_thousand_separator(number)
    if number == 0:
        return 0
    return default


@register.filter
def multiply(number1, number2):
    return number1 * number2


@register.simple_tag
def disk(path: str):
    if path.startswith(("img", "audio", "video")):
        return "{}{}{}".format(CORE_BASE_URL, ASSETS_URL, path)
    if path.startswith("storage"):
        return "{}{}{}".format(CORE_BASE_URL, MEDIA_URL, path)
    return "{}{}{}".format(CORE_BASE_URL, STATIC_URL, path)
