import datetime

import jdatetime

from CONSTANTS import ENGLISH_MONTHS, PERSIAN_MONTHS

dt = datetime
jdt = jdatetime


def format_time(hour: int, minute: int) -> str:
    return "{:02}:{:02}".format(hour, minute)


def format_date_text(
    day: str,
    month: str,
    year: str = "",
    time_text: str = "",
    lang: str = "Persian",
) -> str:
    if lang == "Persian":
        date_text: str = "{} {}".format(day, month) + (" {}".format(year) if year else "")
        return date_text + (" - ساعت {}".format(time_text) if time_text else "")
    else:
        date_text: str = "{} {}".format(month, day) + (", {}".format(year) if year else "")
        return date_text + (" at {}".format(time_text) if time_text else "")


def dt_to_text(
    datetime_obj: datetime.datetime,
    time_check: bool = True,
    year_check: bool = True,
    lang: str = "Persian",
) -> str:
    if not datetime_obj:
        return ""

    # Convert date to datetime if necessary
    if isinstance(datetime_obj, dt.date) and not isinstance(datetime_obj, dt.datetime):
        datetime_obj = dt.datetime.combine(datetime_obj, dt.datetime.min.time())

    if lang == "Persian":
        jalali: jdt.datetime = jdt.datetime.fromgregorian(datetime=datetime_obj)
        day: str = str(jalali.day)
        month: str = PERSIAN_MONTHS[jalali.month]
        year: str = str(jalali.year)
        hour: int = jalali.hour
        minute: int = jalali.minute
    else:
        day: str = str(datetime_obj.day)
        month: str = ENGLISH_MONTHS[datetime_obj.month]
        year: str = str(datetime_obj.year)
        hour: int = datetime_obj.hour
        minute: int = datetime_obj.minute

    time_text: str = format_time(hour, minute) if time_check else ""
    year_text: str = year if year_check else ""

    return format_date_text(day, month, year_text, time_text, lang)
