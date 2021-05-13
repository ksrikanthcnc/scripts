import ntpath
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
import winshell

def Log(*msgs):
    log = open(LOGFILE, "a+")
    for msg in msgs:
        print(msg, end='')
        log.write(str(msg))
    log.write('\n')
    print('')
    log.close()

def GetFileList():
    filenames = []
    for folderpath in PICFOLDER:
        for path, _, files in os.walk(os.path.abspath(folderpath)):
            for file in files:
                if file.endswith('.png') or file.endswith('.jpg'):
                    filenames.append(os.path.join(path, file))
                    # print(os.path.join(path, file))
                else:
                    print('Not image',file)
            # Comment to use recursive files
            break
    return filenames

def UpdateWithHist(filenames):
    global WPIndex
    global WPlist
    if os.path.exists(HISTFILE):
        fHist = open(HISTFILE, 'r')
        for line in fHist.read().splitlines():
            if os.path.exists(line):
                file = line
                try:
                    filenames.remove(file)
                    WPlist.append(file)
                    WPIndex += 1
                except ValueError:
                    Log('{0} in Hist not found in current search area'.format(file))
            elif '--------------' in line:
                filenames = GetFileList()
                WPlist = []
                WPIndex = -1
        if WPIndex > 0: 
            WPIndex += 1
            WPIndex -= SIZE
        Log('History size:', len(WPlist))
        if len(WPlist) % SIZE != 0:
            for _ in range(SIZE - len(WPlist) % SIZE):
                WPlist.insert(0, BLACKPATH)
                WPIndex += 1
    return filenames

def LogWP(filepaths):
    log = open(HISTFILE, "a+")
    time = datetime.datetime.now()
    log.write("TIME : "+str(time)+'\n')
    for file in filepaths:
        log.write(file+'\n')
    log.close()

def SetNewWP():
    Log('New Wallpaper')
    global WPlist
    global WPIndex
    filepaths = GetRandom()
    LogWP(filepaths)
    WPlist.extend(filepaths)
    SetWP(filepaths)

def GetRandom():
    global filenames
    global SIZE
    global GridDim
    if len(filenames) < SIZE:
        LogWP(['---------------------------------'])
        filenames = GetFileList()
        if len(filenames) >= SIZE:
            Log('>>>Finished one cycle, restarting<<<')
        else:
            Log('<<<Grid needs more images than available in given path, using 1x1')
            GridDim = [1,1]
            SIZE = 1            
    Log('Random Sampling {0} from {1} files'.format(SIZE, len(filenames)))
    rdfiles = random.sample(filenames, SIZE)
    for file in rdfiles:
        filenames.remove(file)
    return rdfiles

shell = winshell.shortcut()
def CreateShortcuts(filepaths,shpath):
    for filename in os.listdir(shpath):
        file_path = os.path.join(shpath, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    for i,filepath in enumerate(filepaths):
        shpath = SHPATH + "\\{0}.{1}.lnk".format(i+1,os.path.splitext(os.path.basename(filepath))[0])
        shell.lnk_filepath = shpath
        shell.path = filepath
        shell.write()

def SetWP(filepaths):
    if DryRun:
        for p in filepaths:
            print(p)
        return
    Log('Setting Wallpaper')
    pathgrid = MakeGridPath(filepaths)
    CreateShortcuts(filepaths,SHPATH)
    if pathgrid is not None:
        wallpaper = MakeGridImage(pathgrid)
        cv2.imwrite(WPPATH, wallpaper)
        SPI_SETDESKWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, WPPATH, 0)
        Log('Wallpaper set!')
    else:
        Log('>>>Wallpaper NOT set!')

def MakeGridPath(filepaths):
    if len(filepaths) < SIZE:
        Log('>>>len(grid)[{0}] < SIZE[{1}]'.format(len(filepaths),SIZE))
        return None
    else:
        paths = []
        for path in filepaths:
            if not os.path.exists(path):
                path = BLACKPATH
            im = cv2.imread(path)
            im = cv2.copyMakeBorder(im, PAD, PAD, PAD, PAD, cv2.BORDER_CONSTANT, None, 0)
            paths.append(im)
        grid = []
        for row in range(GridDim[0]):
            finalCol = []
            for col in range(GridDim[1]):
                finalCol.append(paths[row*GridDim[1]+col])
            grid.append(finalCol)
        return grid

def MakeGridImage(cv2Grid):
    interpolation = cv2.INTER_CUBIC
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
        hjoined = [hjoin(row) for row in cv2Grid]
        vjoined = vjoin(hjoined)
        final = vjoined
    else:
        vjoined = [vjoin(row) for row in cv2Grid]
        hjoined = hjoin(vjoined)
        final = hjoined
    return final

def NextWP(sysTrayIcon=None):
    global WPIndex
    global ViewIndex
    if WPIndex == -1:
        WPIndex = -SIZE
    WPIndex += SIZE
    if len(WPlist) == 0 or len(WPlist) == WPIndex:
        Log('\tNext Wallpaper [{0}/{1}/{2}]'.format(WPIndex//SIZE+1,len(WPlist)//SIZE+1,len(filenames)//SIZE))
        SetNewWP()
    else:
        Log('\tNext Wallpaper [{0}/{1}/{2}]'.format(WPIndex//SIZE+1,len(WPlist)//SIZE,len(filenames)//SIZE))
        if WPIndex < -1 and DryRun:
            print('here2')
            exit()
        SetWP(WPlist[WPIndex:WPIndex+SIZE])
    ViewIndex = -1

def PrevWP(sysTrayIcon=None):
    global WPIndex
    global ViewIndex
    if WPIndex == -SIZE or WPIndex == 0:
        WPIndex = -1
    elif WPIndex != -1:
        WPIndex -= SIZE
    elif WPIndex < -1:
        print('here3')
        exit()
    Log('\tPrev Wallpaper [{0}/{1}/{2}]'.format(WPIndex//SIZE+1,len(WPlist)//SIZE,len(filenames)//SIZE))
    if WPlist == []:
        Log('>>>No wallpapers in list, use next wallpaper')
    else:
        if WPIndex == -1:
            Log('Reached first wallpaper in stack, no more previous exist')
            if DryRun:
                print('Black wallpaper')
            else:
                SPI_SETDESKWALLPAPER = 20
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETDESKWALLPAPER, 0, BLACKPATH, 0)
        else:
            # print("{0}[{1}:{1}+{2}]".format(len(WPlist),WPIndex,SIZE))
            SetWP(WPlist[WPIndex:WPIndex+SIZE])
    ViewIndex = -1

cleared = False
def ClearWP(sysTrayIcon=None):
    global cleared
    if cleared:
        Log('WP-ing (restoring)')
        path = WPPATH
    else:
        Log('Black-ing')
        path = BLACKPATH
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, path, 0)
    cleared = not cleared

def ViewNextWP(sysTrayIcon=None):
    global ViewIndex
    if WPIndex < 0:
        Log('Nothing to show, cleared bg')
    else:
        paths = WPlist[WPIndex:WPIndex+SIZE]
        ViewIndex += 1
        if ViewIndex >= len(paths):
            ViewIndex = 0
        available = 0
        for path in paths:
            if os.path.exists(path):
                available += 1
        if available != 0:
            Log('View wallpaper {0}/{1}'.format(ViewIndex+1, len(paths)))
            if not os.path.exists(paths[ViewIndex]):
                ViewNextWP()
            subprocess.run(['explorer', paths[ViewIndex]])
        else:
            Log('All wallpapers deleted in this set')

def ViewPrevWP(sysTrayIcon=None):
    global ViewIndex
    if WPIndex < 0:
        Log('Nothing to show, cleared bg')
    else:
        paths = WPlist[WPIndex:WPIndex+SIZE]
        ViewIndex -= 1
        if ViewIndex < 0:
            ViewIndex = len(paths) - 1
        available = 0
        for path in paths:
            if os.path.exists(path):
                available += 1
        if available != 0:
            Log('View wallpaper {0}/{1}'.format(ViewIndex+1, len(paths)))
            if not os.path.exists(paths[ViewIndex]):
                ViewPrevWP()
            subprocess.run(['explorer', paths[ViewIndex]])
        else:
            Log('All wallpapers deleted in this set')

def WPChanger(stime=300):
    import time
    #ClearWP()
    time.sleep(stime)
    while True:
        if not cleared:
            NextWP()
        time.sleep(stime)

# def Quit():
#     systray.shutdown()
#     exit()

def SysTrayQuit(sysTrayIcon):
    Log('Quitting from systray')
    os._exit(1)
    # Quit()

def ExitFromHotkeys():
    global is_alive
    stop_checking_hotkeys()
    is_alive = False
    # Quit()
    systray.shutdown()
    exit()

PICFOLDER = [
    # r'C:\Users\Kalyanam\Pictures\latest\\',
    r'E:\Drive\Wallpapers\\'
    ]
WORKROOT = r'E:\Pics'
HISTFILE = rf'{WORKROOT}\WallpaperHistory.txt'
LOGFILE = rf'{WORKROOT}\WallpaperLog.txt'
WPPATH = rf'{WORKROOT}\Wallpaper.jpg'
BLACKPATH = rf'{WORKROOT}\black.jpg'
SHPATH = rf'{WORKROOT}\WPs'
if not os.path.exists(SHPATH):
    os.makedirs(SHPATH)

import sys
if len(sys.argv) > 1:
	GridDim = [int(_) for _ in sys.argv[1].split(',')]
else:
	GridDim = [3, 3]
SIZE = GridDim[0] * GridDim[1]
PAD = 20
WPlist = []
WPIndex = -1
ViewIndex = -1

filenames = []
filenames = GetFileList()
filenames = UpdateWithHist(filenames)
DryRun = False

menu_options = (
    ('Prev Wallpaper', None, PrevWP),
    ('Next Wallpaper', None, NextWP),
    ('View NWallpaper', None, ViewNextWP),
    ('View PWallpaper', None, ViewPrevWP),
    ('Clear Wallpaper', None, ClearWP)
    # ('Config', None, config)
)

bindings = [
    [["control", "alt", "q"], None, ExitFromHotkeys],
    [["control", "alt", "n"], None, NextWP],
    [["control", "alt", "p"], None, PrevWP],
    [["control", "alt", "v"], None, ViewNextWP],
    [["control", "shift", "v"], None, ViewPrevWP],
    [["control", "alt", "c"], None, ClearWP]
]

t1 = threading.Thread(target=WPChanger)
t1.start()

systray = SysTrayIcon(r'.\wallpaper.ico',
                      hover_text="Wallpaper Setter", menu_options=menu_options, on_quit=SysTrayQuit)
systray.start()

is_alive = True
register_hotkeys(bindings)
start_checking_hotkeys()
while is_alive:
    time.sleep(0.1)
