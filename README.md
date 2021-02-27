Find_Desktop_Background.vbs
References:
    https://www.tenforums.com/tutorials/39548-add-desktop-background-file-location-context-menu-windows-8-10-a.html
Usage: Open to get the path to current wallpaper and open it in default image viewer

randommov.py
Prerequisites:
    adjust ffmpeg, vlc paths and locations to movies
Usage:
    Run the script to list random movie
        'y' to play it
        'q' to quit
        '<enter/return>' to list next one
        '<number>' play the movie with this number

randomwp.py
References:
    https://www.geeksforgeeks.org/concatenate-images-using-opencv-in-python/
Prerequisites:
    python module: 'infi.systray'
    update paths, and adjust grid size as required (blackpath is used to hide current wallpaper)
Usage:
    run the script
    Initially clears (and sets blackpath image as wallpaper)
    Creates systray (can use wallpaper.ico)
    ctrl + alt + q  Quit
               + n  Next Wallpaper
               + p  Previous wallpaper
               + c  Clear Wallpaper (relace with blackpath)
               + v  View current set of wallpapers, one by one (use again to cycle)
    ctrl + shift + v    View previous wallpaper in cycle
Note:
    run with pythonw.exe to not get the terminal

wh tagger.py
References:
    https://stackoverflow.com/a/10075210/6676945
Prerequisites:
    python module 'wallhaven'
    'exiftool' to edit tags
    Update paths
    provide API key if needed
Usage:
    run sript to update tags of wallhaven-<id>.jpg files in given path

flat course.sh
Prerequisites:
    Check the code and adjust before using
Usage:
    run with path to hierarchial course, script will flatten it out with naming as 01_01_01, ...
