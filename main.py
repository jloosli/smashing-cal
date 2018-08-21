import datetime
import os
import platform
import re
import subprocess
from functools import lru_cache

import requests

from bs4 import BeautifulSoup

import cal_search
import download_files

CAL_STORAGE = os.path.expanduser('~/calendars')
SIZE_RE = re.compile(r'(?P<width>\d+)[×xX](?P<height>\d+)')


def check_calendars():
    """Check to see if the current calendars are up to date"""
    if not os.path.exists(CAL_STORAGE):
        os.makedirs(CAL_STORAGE)

    file_has_current_date_string_regex = re.compile(r'^' + date_string())
    files = [f for f in os.listdir(CAL_STORAGE) if os.path.isfile(os.path.join(CAL_STORAGE, f))]
    return len(files) and file_has_current_date_string_regex.match(files[0])


@lru_cache(maxsize=None)
def date_string(date=None):
    """ Returns Mon-YYYY string (used to format filenames so they're consistentently named) """
    if not date:
        date = datetime.datetime.now()
    return date.strftime("%b-%Y")


def rotate_calendar():
    if platform.system() == 'Windows':
        rotate_calendar_win(platform.release())
    else:
        rotate_calendar_linux()


def rotate_calendar_win(version):
    import winreg
    from win32.constants import HWND_BROADCAST, WM_SETTINGCHANGE
    from win32.api import SendMessage
    from time import sleep
    desktop_key = r'Control Panel\Desktop'
    wallpaper_key = r'Wallpaper'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, desktop_key) as key:
        current_background, type = winreg.QueryValueEx(key, wallpaper_key)
        print("Current background: {}".format(current_background))
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, desktop_key, 0, winreg.KEY_WRITE) as key:
        files = calendar_files()
        try:
            idx = files.index(current_background) + 1
            if idx == len(files):
                idx = 0
        except ValueError:
            idx = 0
        print("Setting background to: {}".format(files[idx]))
        winreg.SetValueEx(key, wallpaper_key, 0, winreg.REG_SZ, files[idx])
    # notify the system about the changes
    SendMessage(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment')
    update_request = 'RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters'
    sleep(1)
    subprocess.Popen(update_request)
    sleep(1)
    subprocess.Popen(update_request)


def rotate_calendar_linux():
    """ Changes current background to the next file in directory """
    current_background_request = 'gsettings get org.gnome.desktop.background picture-uri'.split()

    process = subprocess.Popen(current_background_request, stdout=subprocess.PIPE)
    current_background, error = process.communicate()
    if current_background:
        current_background = current_background.decode('utf-8').split("'")[1].split('file://')[1]
        print("Current background: {}".format(current_background))
    files = calendar_files()
    try:
        idx = files.index(current_background) + 1
        if idx == len(files):
            idx = 0
    except ValueError:
        idx = 0
    print("Setting background to: {}".format(files[idx]))
    set_background_request = 'gsettings set org.gnome.desktop.background picture-uri file://{}' \
        .format(files[idx]).split()
    set_environment()
    subprocess.Popen(set_background_request)


def get_calendars(args):
    """
    - Looks up latest url for calendars and finds all 'with calendar links'
    - Runs through the links to find the best match given the desired height and width
    """
    cals_to_download = []
    try:
        url = cal_search.calendar_url(args.date)
        print("Looking up calendars on {}".format(url))
        response = requests.get(url).text
        soup = BeautifulSoup(response, 'lxml')
        links = soup.find(id='main').find('article').find_all('li')
        cal_groups = [li for li in links if 'without calendar' in li.text]
        ideal_ratio = args.width / args.height
        for group in cal_groups:
            best_match = {'w': 0, 'h': 1, 'url': ''}
            cals = [t for t in group.find_all('a') if SIZE_RE.match(t.text)]
            for cal in cals:
                match = re.search(SIZE_RE, cal.text)
                if match:
                    w = int(match.group('width'))
                    h = int(match.group('height'))
                    if w < args.width or h < args.height:
                        '''Don't even look at smaller widths or heights'''
                        continue
                    if w == args.width and h == args.height:
                        '''If you found the exact parameters, go with it'''
                        best_match['url'] = cal['href']
                        break
                    ratio = w / h
                    best_ratio = best_match['w'] / best_match['h']
                    ratio_diff = abs(ratio - ideal_ratio)
                    best_diff = abs(best_ratio - ideal_ratio)
                    if ratio_diff < best_diff:
                        best_match = {'w': w, 'h': h, 'url': cal['href']}
            if best_match['url']:
                cals_to_download.append(best_match['url'])
        print("Found {} calendars to download".format(len(cals_to_download)))
    except requests.exceptions.ConnectionError:
        print("Could not connect to Smashing Magazine")
    if len(cals_to_download):
        remove_calandars()
        download_calendars(cals_to_download)


def download_calendars(calendars):
    """Asynchronous download of calendars"""
    download_files.download(calendars, CAL_STORAGE, date_string())


def remove_calandars():
    """Remove all the files from existing calendar directory"""
    for file_path in calendar_files():
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)
    calendar_files.cache_clear()


@lru_cache(maxsize=None)
def calendar_files():
    """Latest calendar files"""
    files = []
    for file in os.listdir(CAL_STORAGE):
        file_path = os.path.join(CAL_STORAGE, file)
        try:
            if os.path.isfile(file_path):
                files.append(file_path)
        except Exception as e:
            print(e)
    return files


@lru_cache(maxsize=None)
def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--width', help='display width', type=int, default=1920)
    parser.add_argument('-t', '--height', help='display height', type=int, default=1080)
    parser.add_argument('-f', '--force', help='force download of calendars', action="store_true")
    parser.add_argument('-d', '--date', help='Date to search', default=None)
    return parser.parse_args()


def set_environment():
    """
    Required when setting gsettings from cron
    See: http://askubuntu.com/questions/483687/editing-gsettings-unsuccesful-when-initiated-from-cron
    """
    session_type = os.environ['XDG_SESSION_TYPE']
    if session_type == 'wayland':
        process_name = 'wayland'
    else:
        process_name = 'gnome-session'
    pids = subprocess.check_output(["pgrep", process_name]).decode("utf-8").split()
    for pid in pids:
        try:
            proc_path = '/proc/{}/environ'.format(pid)
            if not os.access(proc_path, os.R_OK):
                continue
            cmd = "grep -z DBUS_SESSION_BUS_ADDRESS {}|cut -d= -f2-".format(proc_path)
            bus_address = subprocess.check_output(['/bin/bash', '-c', cmd]).decode("utf-8").strip().replace("\0", "")
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = bus_address
            break
        except OSError as err:
            pass

def main():
    start = datetime.datetime.now()
    args = get_args()
    if args.force or not check_calendars():
        get_calendars(args)
    rotate_calendar()
    end = datetime.datetime.now()
    delta = (end - start)
    print("Completed in {}".format(delta))


if __name__ == '__main__':
    main()
