import concurrent.futures
import os
import urllib.request

URLS = ['http://files.smashingmagazine.com/wallpapers/jan-17/angel-in-snow/cal/jan-17-angel-in-snow-cal-1920x1200.jpg',
        'http://files.smashingmagazine.com/wallpapers/jan-17/colorful-2017/cal/jan-17-colorful-2017-cal-1920x1080.png']


def load_url(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as conn:
        return conn.read()


def download_url(url, location='~/tmp', prefix=''):
    name = url.split('/')[-1]
    if prefix:
        name = prefix + '-' + name
    return urllib.request.urlretrieve(url, os.path.join(os.path.expanduser(location), name))


def download(urls, directory='~/tmp', prefix=''):
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {executor.submit(download_url, url, directory, prefix): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            print("Downloaded %s" % url)


if __name__ == '__main__':
    download(URLS)
