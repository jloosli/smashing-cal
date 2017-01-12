from datetime import datetime

from google import search


def calendar_url(date=None):
    if not date:
        return calendar_url(datetime.now())
    search_tpl = 'site:https://www.smashingmagazine.com calendar {}'
    if isinstance(date, datetime):
        search_string = search_tpl.format(date.strftime("%B %Y"))
    else:
        search_string = search_tpl.format(date)

    url = next(search(search_string, stop=10), '')
    return url


if __name__ == '__main__':
    print(calendar_url())
