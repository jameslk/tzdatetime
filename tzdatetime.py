from abc import abstractmethod
from datetime import datetime as Datetime, date as Date, timedelta as Timedelta, \
    tzinfo as Tzinfo
from typing import Callable

from django.utils import timezone as Timezone
import pytz as Pytz

def get_timezone_from(timezone_thing: any) -> Tzinfo:
    timezone_object = Pytz.timezone(timezone_thing) if isinstance(timezone_thing, str) \
        else timezone_thing

    datetime_timezone = Timezone.localtime(Timezone.now(), timezone_object).tzinfo

    return datetime_timezone

class ITimezoneable:
    @abstractmethod
    def to_timezone(self, timezone: any) -> 'ITimezoneable': pass

    @abstractmethod
    def to_datetime(self) -> Datetime: pass

    @abstractmethod
    def is_in_timezone(self, timezone: any): pass

    @abstractmethod
    def get_timezone(self) -> Tzinfo: pass

    @abstractmethod
    def get_timezone_name(self) -> str: pass

    @abstractmethod
    def __add__(self, other: Timedelta) -> 'ITimezoneable': pass

    @abstractmethod
    def __sub__(self, other: Timedelta) -> 'ITimezoneable': pass

    @abstractmethod
    def __eq__(self, other: 'ITimezoneable') -> bool: pass

    @abstractmethod
    def __gt__(self, other: 'ITimezoneable') -> bool: pass

    @abstractmethod
    def __ge__(self, other: 'ITimezoneable') -> bool: pass

    @abstractmethod
    def __lt__(self, other: 'ITimezoneable') -> bool: pass

    @abstractmethod
    def __le__(self, other: 'ITimezoneable') -> bool: pass

class ITimezoneableDate(ITimezoneable):
    @classmethod
    @abstractmethod
    def today(cls) -> 'ITimezoneableDate': pass

    @classmethod
    @abstractmethod
    def today_in_timezone(cls, timezone: any) -> 'ITimezoneableDate': pass

    @abstractmethod
    def to_tz_datetime(self) -> 'TzDatetime': pass

    @abstractmethod
    def to_naive_date(self) -> Date: pass

class TzDatetimeBase(ITimezoneable):
    def __init__(self, date_or_datetime: any, timezone: any = None):
        datetime = date_or_datetime if isinstance(date_or_datetime, Datetime) \
            else Datetime.combine(date_or_datetime, Datetime.min.time())

        assert not (Timezone.is_aware(datetime) and bool(timezone)), \
            'The provided datetime object may be timezone-aware or an explicit' \
            ' timezone may be provided, but not both'

        if timezone:
            self._datetime = Timezone.make_aware(datetime, get_timezone_from(timezone))
        elif not Timezone.is_aware(datetime):
            self._datetime = Timezone.make_aware(datetime)
        else:
            self._datetime = datetime

    @classmethod
    def from_timestamp(cls, timestamp_in_s: int = None, timezone: any = None, timestamp_in_ms: int = None):
        assert timestamp_in_s or timestamp_in_ms,\
            'Either a timestamp in seconds or a timestamp in milliseconds must be provided'

        assert bool(timestamp_in_s) != bool(timestamp_in_ms),\
            'Cannot provide both a timestamp in seconds and a timestamp in milliseconds'

        if timestamp_in_ms:
            timestamp_in_s = timestamp_in_ms / 1e3

        return cls(Datetime.fromtimestamp(timestamp_in_s), timezone)

    def to_timezone(self, timezone: any) -> 'ITimezoneable':
        timezone = get_timezone_from(timezone)
        return self.__class__(Timezone.localtime(self._datetime, timezone))

    def to_datetime(self) -> Datetime:
        return self._datetime

    def is_in_timezone(self, timezone: any):
        other_timezone = get_timezone_from(timezone)
        assert other_timezone, 'No timezone provided'
        return self._datetime.tzinfo == other_timezone

    def get_timezone(self) -> Tzinfo:
        return self._datetime.tzinfo

    def get_timezone_name(self) -> str:
        return self._datetime.tzinfo.tzname(self._datetime)

    def __str__(self):
        return str(self._datetime)

    def __add__(self, other: Timedelta) -> 'ITimezoneable':
        return self.__class__(self._datetime + other)

    def __sub__(self, other: Timedelta) -> 'ITimezoneable':
        return self.__class__(self._datetime - other)

    def __eq__(self, other: 'ITimezoneable') -> bool: return self._compare(other, lambda a, b: a == b)
    def __gt__(self, other: 'ITimezoneable') -> bool: return self._compare(other, lambda a, b: a > b)
    def __ge__(self, other: 'ITimezoneable') -> bool: return self._compare(other, lambda a, b: a >= b)
    def __lt__(self, other: 'ITimezoneable') -> bool: return self._compare(other, lambda a, b: a < b)
    def __le__(self, other: 'ITimezoneable') -> bool: return self._compare(other, lambda a, b: a <= b)

    def _compare(self, other: 'ITimezoneable', datetime_comparator: Callable) -> bool:
        return datetime_comparator(self._datetime, other.to_datetime())

class TzDatetime(TzDatetimeBase):
    @classmethod
    def now(cls) -> 'TzDatetime':
        return cls(Timezone.now())

    @classmethod
    def now_in_timezone(cls, timezone: any) -> 'TzDatetime':
        return cls(Timezone.now()).to_timezone(timezone)

    def to_tz_date(self) -> 'TzDate':
        return TzDate(self._datetime)

class TzDate(ITimezoneableDate, TzDatetimeBase):
    @classmethod
    def today(cls) -> 'TzDate':
        return cls(Timezone.now().date())

    @classmethod
    def today_in_timezone(cls, timezone: any) -> 'TzDate':
        timezone = get_timezone_from(timezone)
        return cls(Timezone.localtime(Timezone.now(), timezone).date(), timezone)

    def to_tz_datetime(self) -> 'TzDatetime':
        return TzDatetime(self._datetime)

    def to_naive_date(self) -> Date:
        return self._datetime.date()

class TzRelativeDate(ITimezoneableDate):
    def __init__(self, days_since_today: int = 0, timezone: any = None):
        self._days_since_today = days_since_today
        self._timezone = get_timezone_from(timezone)

    @classmethod
    def today(cls) -> 'ITimezoneableDate':
        return cls()

    @classmethod
    def today_in_timezone(cls, timezone: any) -> 'ITimezoneableDate':
        return cls(timezone=timezone)

    @classmethod
    def from_tz_date(cls, tz_date: TzDate):
        timezone = tz_date.get_timezone()
        todays_date = TzDate.today_in_timezone(timezone).to_naive_date()
        duration = tz_date.to_naive_date() - todays_date
        return cls(duration.days, timezone)

    @classmethod
    def from_naive_date(cls, naive_date: Date, timezone: Tzinfo):
        return cls.from_tz_date(TzDate(naive_date, timezone))

    def to_tz_datetime(self) -> 'TzDatetime':
        todays_date = Timezone.localtime(Timezone.now(), self._timezone).date()
        shifted_date = todays_date + Timedelta(days=self._days_since_today)
        shifted_datetime = Datetime.combine(shifted_date, Datetime.min.time())
        return TzDatetime(shifted_datetime, self._timezone)

    def to_datetime(self) -> Datetime:
        return self.to_tz_datetime().to_datetime()

    def to_naive_date(self) -> Date:
        return self.to_datetime().date()

    def to_timezone(self, timezone: any) -> 'ITimezoneable':
        return self.__class__(self._days_since_today, timezone)

    def is_in_timezone(self, timezone: any):
        return self._timezone == timezone

    def get_timezone(self) -> Tzinfo:
        return self._timezone

    def get_timezone_name(self) -> str:
        datetime = self.to_datetime()
        return datetime.tzinfo.tzname(datetime)

    def __add__(self, other: Timedelta) -> 'ITimezoneable':
        return self.__class__(self._days_since_today + other.days, self._timezone)

    def __sub__(self, other: Timedelta) -> 'ITimezoneable':
        return self.__class__(self._days_since_today - other.days, self._timezone)

    def __eq__(self, other: 'ITimezoneable') -> bool: return self._compare(other, lambda a, b: a == b)
    def __gt__(self, other: 'ITimezoneable') -> bool: return self._compare(other, lambda a, b: a > b)
    def __ge__(self, other: 'ITimezoneable') -> bool: return self._compare(other, lambda a, b: a >= b)
    def __lt__(self, other: 'ITimezoneable') -> bool: return self._compare(other, lambda a, b: a < b)
    def __le__(self, other: 'ITimezoneable') -> bool: return self._compare(other, lambda a, b: a <= b)

    def _compare(self, other: 'ITimezoneable', datetime_comparator: Callable) -> bool:
        return datetime_comparator(self.to_datetime(), other.to_datetime())
