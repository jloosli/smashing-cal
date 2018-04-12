from datetime import datetime

from googlesearch import search


def calendar_url(date=None, limit_to_last_month=False):
    if not date:
        return calendar_url(datetime.now(), limit_to_last_month=True)
    search_tpl = 'calendar {}'

    if isinstance(date, datetime):
        search_string = search_tpl.format(date.strftime("%B %Y"))
    else:
        search_string = search_tpl.format(date)

    extra_args = {
        'num': 1,
        'domains': ['https://www.smashingmagazine.com']
    }
    if limit_to_last_month:
        extra_args['tbs'] = 'qdr:m'
    url = next(search(search_string, **extra_args), '')
    return url


if __name__ == '__main__':
    print(calendar_url())
