from typing import Dict

# Time limits (in seconds)
MINUTE: int = 60
HOUR: int = 60 * MINUTE
DAY: int = 24 * HOUR
ADMIN_SESSION_COOKIE_AGE: int = 3 * DAY
USER_SESSION_FULL_AGE: int = 30 * DAY
USER_SESSION_RENEWAL_AGE: int = 3 * DAY
VERIFICATION_CODE_CACHE_AGE: int = 5 * MINUTE
WORKER_WAIT: int = HOUR
UNSUCCESSFUL_LOGIN_COUNT_CACHE_AGE: int = 4 * HOUR

# Cache key prefixes for Redis
USER_SESSION_KEY_PREFIX: str = ":2:user-auth-token-"
VERIFICATION_CODE_CACHE_PREFIX: str = ":3:vcode-"
UNSUCCESSFUL_LOGIN_COUNT_CACHE_PREFIX: str = ":3:unsuccessful-login-"
GET_QUERY_FILTER_SEARCH_PREFIX: str = "filter__"

# Rate limits and pagination
PAGINATE_PAGE_SIZE: int = 30
ANONYMOUS_THROTTLE_RATES_PER_HOUR: int = 300
USER_THROTTLE_RATES_PER_HOUR: int = 4000
VERIFICATION_CODE_THROTTLE_RATES_PER_HOUR: int = 15
MAX_UNSUCCESSFUL_LOGIN_COUNT: int = 5

# External API configuration

# Financial constants (amounts in Iranian Toman)
MINIMUM_TRANSACTION_AMOUNT_FOR_SKIP: int = 100
VA_TAX_PERCENTAGE: float = 0.1


# String mappings for number and date conversion
PERSIAN_ENGLISH_NUMS: Dict[str, str] = {
    "۰": "0",
    "۱": "1",
    "۲": "2",
    "۳": "3",
    "۴": "4",
    "۵": "5",
    "۶": "6",
    "۷": "7",
    "۸": "8",
    "۹": "9",
}

# Persian (Jalali) month names
PERSIAN_MONTHS: Dict[int, str] = {
    1: "فروردین",
    2: "اردیبهشت",
    3: "خرداد",
    4: "تیر",
    5: "مرداد",
    6: "شهریور",
    7: "مهر",
    8: "آبان",
    9: "آذر",
    10: "دی",
    11: "بهمن",
    12: "اسفند",
}

# Gregorian month names
ENGLISH_MONTHS: Dict[int, str] = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}
