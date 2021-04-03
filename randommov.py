import os
import random as rd
import subprocess
import time

def fdur(filename):
    result = subprocess.run([r'G:\My Files\Utiities\ffmpeg-n4.3.1-20-g8a2acdc6da-win64-gpl-4.3\bin\ffprobe.exe', "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", "-sexagesimal", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return (result.stdout).decode("utf-8").rstrip()[:4]

try:
    paths = []
    paths.append("G:\DownLoads\Video\Movies\\")
    paths.append("G:\DownLoads\Video\Fresh\\")
    paths.append("F:\Movies\Eng\\")
    paths.append("F:\Movies\Eng\\nosubs\\")
    # paths.append("F:\Movies\Eng")

    movls = []
    for path in paths:
        for name in os.listdir(path):
            if name.endswith(".mp4") or name.endswith(".avi") or name.endswith(".mkv"):
                movls.append(path+name)
    print('Total:', len(movls))
    movlss = list(movls)

    run = False
    watchlist = []
    print('[Enter] to suggest next')
    print('[y] to play the last movie')
    print('[q] to quit')
    print('[<Enter a number>] to play that movie')
    print('')
    while not run:
        if len(movls) != 0:
            mov = str(rd.choice(movls))
            movls.remove(mov)
            watchlist.append(mov)
            print(str(len(watchlist))+'.',end=' ')
            print('['+str(fdur(mov))+']',end=' ')
            print(os.path.basename(mov),'\t\t\t',os.path.dirname(mov),end='')
        else:
            print('All movies listed, make up your mind!!!', end='')
        play = input()
        if play == 'y':
            run = True
        elif play == 'q':
            exit()
        elif play.isnumeric():
            play = int(play)
            if play < len(watchlist):
                mov = watchlist[play-1]
                run = True
            else:
                print('Enter number in bounds')
    print('playing', mov)
    e = subprocess.Popen(r'explorer /select,'+mov)
    time.sleep(1)
    v = subprocess.Popen(["C:/Program Files (x86)/VideoLAN/VLC/vlc.exe", mov])

except:
    import sys
    print("Unexpected error:", sys.exc_info()[0])
    print("Unexpected error:", sys.exc_info()[1])
