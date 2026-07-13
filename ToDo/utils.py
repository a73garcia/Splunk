from datetime import datetime

DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"


def today():
    return datetime.now().strftime(DATE_FORMAT)


def now():
    return datetime.now().strftime(DATETIME_FORMAT)


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default
