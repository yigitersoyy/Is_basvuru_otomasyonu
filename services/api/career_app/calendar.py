"""National public holidays; regional and employer-specific calendars require review."""

from functools import lru_cache

import holidays


@lru_cache(maxsize=100)
def national_calendar(country, year):
    return holidays.country_holidays(country, years=[year], observed=True)


def business_day(date, country):
    return date.weekday() < 5 and date not in national_calendar(country, date.year)
