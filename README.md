# tzdatetime

## Why does this exist?

To solve the issue of timezones getting stripped off date objects and to make
conversions between timezones easier.

Everything is handled with timezone-aware datetime objects internally,
even for dates without time.

TzRelativeDate allows for creating dates relative to today, so that when converting
to a different timezone, a relative date still represents "today" in that timezone.

https://docs.djangoproject.com/en/1.10/topics/i18n/timezones/#troubleshooting § 3

## Notes

I have not written tests against this library, as it was a quick solution
to a common problem. It not maintained on PyPI. I use it mostly for
internal purposes.
