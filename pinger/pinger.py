import subprocess
from infi.systray import SysTrayIcon
import os
import time
import winsound

def SysTrayQuit(sysTrayIcon):
    os._exit(1)
    # Quit()
    pass


def Refresh(sysTrayIcon):
    pass


menu_options = (
    ('Refresh', None, Refresh),
    # ('Config', None, config)
)

systray = SysTrayIcon(r'H:\temp\ping\yellow.ico',
                      hover_text="Wallpaper Setter", menu_options=menu_options, on_quit=SysTrayQuit)
systray.start()

print('Started')
prev = 1
while True:
    time.sleep(1)
    output = subprocess.call(['ping', '-n', '1', '8.8.8.8'],stdout=subprocess.DEVNULL)
    # output = subprocess.call(['ping', '-n', '1', '8.8.8.8'])
    if output == 0:
        systray.update(icon=r'H:\temp\ping\green.ico')
    elif output == 1:
        systray.update(icon=r'H:\temp\ping\red.ico')
    else:
        systray.update(icon=r'H:\temp\ping\yellow.ico')

    if prev != output:
        if output == 0:
            print('Connected')
            for i in range(2):
                winsound.Beep(2000,500)
                time.sleep(500)
        else:
            print('Disconnected')
            for i in range(2):
                winsound.Beep(1000,500)
                time.sleep(500)
    prev = output

# systray.shutdown()
