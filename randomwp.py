import time
from global_hotkeys import *
import itertools
import glob
from os import walk
import random
import cv2
import ctypes
import os
import datetime
from pynput import keyboard
from infi.systray import SysTrayIcon
import threading
import win32gui
import subprocess

import sys


def makeimg(grid):
    interpolation = cv2.INTER_CUBIC
    # if 'cv2' not in sys.modules:
    #     import cv2

    def hjoin(imgs):
        h_min = min(img.shape[0] for img in imgs)
        resized_imgs = []
        for img in imgs:
            dim = (int(img.shape[1] * h_min / img.shape[0]), h_min)
            resized_img = cv2.resize(img, dim, interpolation=interpolation)
            resized_imgs.append(resized_img)
        return cv2.hconcat(resized_imgs)

    def vjoin(imgs):
        w_min = min(img.shape[1] for img in imgs)
        resized_imgs = []
        for img in imgs:
            dim = (w_min, int(img.shape[0] * w_min / img.shape[1]))
            resized_img = cv2.resize(img, dim, interpolation=interpolation)
            resized_imgs.append(resized_img)
        return cv2.vconcat(resized_imgs)

    if True:
        hjoined = [hjoin(row) for row in grid]
        vjoined = vjoin(hjoined)
        final = vjoined
    else:
        vjoined = [vjoin(row) for row in grid]
        hjoined = hjoin(vjoined)
        final = hjoined
    return final


def getrandom(path):
    log('Random Sampling {0}'.format(rows*cols))
    _, _, filenames = next(walk(path))
    rdfiles = random.sample(filenames, rows*cols)
    filepaths = []
    for file in rdfiles:
        filepaths.append(os.path.join(os.path.abspath(path), file))
    return filepaths


def makepathgrid(filepaths):
    paths = []
    for path in filepaths:
        if not os.path.exists(path):
            path = blackpath
        paths.append(cv2.imread(path))
    grid = []
    for row in range(rows):
        finalCol = []
        for col in range(cols):
            finalCol.append(paths[row*cols+col])
        grid.append(finalCol)
    return grid


def logwallpaper(filepaths):
    log = open(logpath, "a")
    time = datetime.datetime.now()
    log.write("TIME : "+str(time)+'\n')
    for file in filepaths:
        log.write(file+'\n')
    log.close()


def log(*msgs):
    log = open(logFile, "a")
    for msg in msgs:
        print(msg, end='')
        log.write(msg)
    log.write('\n')
    print('')
    log.close()


def setwallpaper(filepaths):
    log('   Setting Wallpaper')
    pathgrid = makepathgrid(filepaths)
    wallpaper = makeimg(pathgrid)
    cv2.imwrite(wppath, wallpaper)
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, wppath, 0)
    log('   Wallpaper set!')


def fillhistory():
    destpath = r'C:\Users\Kalyanam\Pictures\groupedwallpaper.txt'
    log = open(destpath, "r")
    histbatch = []
    hist = []
    for line in log:
        if "Wallpapers" not in line:
            if histbatch != []:
                hist.append(histbatch)
            histbatch = []
        else:
            histbatch.append(line[:-1])
    if histbatch != []:
        hist.append(histbatch)
    global wpset
    wpset = hist


def freshwallpaper():
    log('Fresh Wallpaper')
    global wpset
    global wpindex
    filepaths = getrandom(path)
    logwallpaper(filepaths)
    wpset.append(filepaths)
    setwallpaper(filepaths)


def nextwallpaper(sysTrayIcon=None):
    global wpindex
    global wpset
    global pathindex
    pathindex = -1
    wpindex += 1
    if wpindex == len(wpset):
        freshwallpaper()
    else:
        if wpindex < 0:
            wpindex = 0
        setwallpaper(wpset[wpindex])
    log('Next Wallpaper {0}/{1}'.format(wpindex+1, len(wpset)))
    # sysTraytext = 2/1


def prevwallpaper(sysTrayIcon=None):
    global wpindex
    global wpset
    if wpset == []:
        freshwallpaper()
    else:
        wpindex -= 1
        if wpindex <= -1:
            log('Reached first wallpaper in stack, no more previous exist')
            wpindex = -1
            SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, blackpath, 0)
        else:
            setwallpaper(wpset[wpindex])
    log('Prev Wallpaper {0}/{1}'.format(wpindex+1, len(wpset)))


cleared = False
def clearwallpaper(sysTrayIcon=None):
    global cleared
    if cleared:
        log('WP-ing (restoring)')
        path = wppath
    else:
        log('Black-ing')
        path = blackpath
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, path, 0)
    cleared = not cleared


def viewnextwallpaper(sysTrayIcon=None):
    global pathindex
    paths = wpset[wpindex]
    pathindex += 1
    if pathindex >= len(paths):
        pathindex = 0
    if wpindex == -1:
        log('Nothing to show, cleared bg')
    else:
        available = 0
        for path in paths:
            if os.path.exists(path):
                available += 1
        if available != 0:
            log('View wallpaper {0}/{1}'.format(pathindex, len(paths)))
            if not os.path.exists(paths[pathindex]):
                viewnextwallpaper()
            subprocess.run(['explorer', paths[pathindex]])
        else:
            log('All wallpapers deleted in this set')

def viewprevwallpaper(sysTrayIcon=None):
    global pathindex
    paths = wpset[wpindex]
    pathindex -= 1
    if pathindex < 0:
        pathindex = len(paths) - 1
    if wpindex == -1:
        log('Nothing to show, cleared bg')
    else:
        available = 0
        for path in paths:
            if os.path.exists(path):
                available += 1
        if available != 0:
            log('View wallpaper {0}/{1}'.format(pathindex, len(paths)))
            if not os.path.exists(paths[pathindex]):
                viewprevwallpaper()
            subprocess.run(['explorer', paths[pathindex]])
        else:
            log('All wallpapers deleted in this set')


# def config(sysTrayIcon=None):
#     proc = subprocess.Popen(['python', 'input(gridsize)'],
#                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     out, err = proc.communicate()
#     print(out, err)


def Quit():
    systray.shutdown()
    exit()


def bye(sysTrayIcon):
    log('Quitting from systray')
    os._exit(1)
    # Quit()


menu_options = (
    ('Prev Wallpaper', None, prevwallpaper),
    ('Next Wallpaper', None, nextwallpaper),
    ('View NWallpaper', None, viewnextwallpaper),
    ('View PWallpaper', None, viewprevwallpaper),
    ('Clear Wallpaper', None, clearwallpaper)
    # ('Config', None, config)
)

systray = SysTrayIcon(r'C:\Users\Kalyanam\Pictures\wallpaper.ico',
                      hover_text="Wallpaper Setter", menu_options=menu_options, on_quit=bye)
systray.start()


def wallpaperchanger(stime=300):
    import time
    clearwallpaper()
    time.sleep(stime)
    while True:
        nextwallpaper()
        time.sleep(stime)


path = r'C:\Users\Kalyanam\Pictures\Wallpapers\\'
logpath = r'C:\Users\Kalyanam\Pictures\WallpaperHistory.txt'
logFile = r'C:\Users\Kalyanam\Pictures\WallpaperLog.txt'
wppath = r'C:\Users\Kalyanam\Pictures\Wallpaper.jpg'
blackpath = r'C:\Users\Kalyanam\Pictures\black.jpg'

gridsize = [3, 3]
rows = gridsize[0]
cols = gridsize[1]
refrshrate = 300
wpset = []
# fillhistory()
wpindex = -1
pathindex = -1

t1 = threading.Thread(target=wallpaperchanger)
t1.start()
# t1.join()

is_alive = True


def exit_application():
    global is_alive
    stop_checking_hotkeys()
    is_alive = False
    Quit()


# Declare some key bindings.
# These take the format of [<key list>, <keydown handler callback>, <keyup handler callback>]
bindings = [
    [["control", "alt", "q"], None, exit_application],
    [["control", "alt", "n"], None, nextwallpaper],
    [["control", "alt", "p"], None, prevwallpaper],
    [["control", "alt", "v"], None, viewnextwallpaper],
    [["control", "shift", "v"], None, viewprevwallpaper],
    # [["control", "alt", "shift", "v"], None, viewprevwallpaper],
    [["control", "alt", "c"], None, clearwallpaper]
]
register_hotkeys(bindings)
start_checking_hotkeys()
while is_alive:
    time.sleep(0.1)
