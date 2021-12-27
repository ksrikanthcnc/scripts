print('Importing')
import argparse
from datetime import datetime
from tkinter import *
import subprocess


parser = argparse.ArgumentParser(description='Config of pinger')
parser.add_argument('--target', type=str, help='ping <tagret>')
parser.add_argument('--size', help='Buffer size')
args = parser.parse_args()

print('Started')
SIZE = args.size and int(args.size) or 50
TARGET = args.target or '8.8.8.8'
ls = ['?']*SIZE

ROOT = Tk()
ROOT.title(TARGET)
ROOT.attributes('-topmost', True)
ROOT.attributes('-alpha', 0.5)

LABEL = Label(ROOT, text="Hello, world!")#, wraplength=SIZE*15)
LABEL.pack()
OTIME = Label(ROOT, text="OldTime")
OTIME.pack()
NTIME = Label(ROOT, text="NewTime")
NTIME.pack()


def update():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    OTIME.config(text=current_time+ls[-1])

    output = subprocess.call(['ping', '-n', '1', TARGET],
                             stdout=subprocess.DEVNULL, creationflags=0x08000000)
    if output == 0:
        output = '='
    elif output == 1:
        output = 'X'
    else:
        output = '?'
    ls.append(output)
    ls.pop(0)

    text = ' '.join(ls)
    LABEL.config(text=text)

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    NTIME.config(text=current_time+ls[-1])

    ROOT.after(1, update)


ROOT.after(100, update)
ROOT.mainloop()

print('Done')
