import subprocess
import os
import json

class ExifTool(object):
    sentinel = "{ready}\r\n"
    def __init__(self, executable=r'G:\My Files\Utiities\exiftool.exe'):
        self.executable = executable
    def __enter__(self):
        self.process = subprocess.Popen(
            [self.executable, "-stay_open", "True",  "-@", "-"],
            universal_newlines=True,
			encoding='utf-8',
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self
    def  __exit__(self, exc_type, exc_value, traceback):
        self.process.stdin.write("-stay_open\nFalse\n")
        self.process.stdin.flush()
    def execute(self, *args):
        args = args + ("-execute\n",)
        self.process.stdin.write(str.join("\n", args))
        self.process.stdin.flush()
        output = ""
        fd = self.process.stdout.fileno()
        while not output.endswith(self.sentinel):
            output += os.read(fd, 4096).decode('utf-8')
        return output[:-len(self.sentinel)]

from pathlib import Path
# rootdir = '/home/srikanth/temp/WH/Wallpapers'
#rootdir = r'H:\temp\wh'
rootdirs = [r'C:\Users\Kalyanam\Pictures\Wallpapers', r'C:\Users\Kalyanam\Pictures\latest']
#rootdir = r'C:\Users\Kalyanam\Pictures\Wallpapers'
#rootdir = r'C:\Users\Kalyanam\Pictures\latest'

paths = []
for rootdir in rootdirs:
	for path in Path(rootdir).rglob('wallhaven*.*'):
		paths.append(path)
paths.sort()
invalids = []
invalid = open('invalid.txt','r+')
for line in invalid.readlines():
	invalids.append(line[:-1])
invalid.close()

taggeds = []
tagged = open('tagged.txt','r+')
for line in tagged.readlines():
	taggeds.append(line[:-1])
tagged.close()

import wallhaven as wh
from wallhaven import Wallhaven
import re
import json
import os
import subprocess
import time
apif = open('whapi.txt')
api=apif.readline()
wallhaven = Wallhaven(api)
wallhaven.REQUEST_TIMEOUT = 0
invalid = open('invalid.txt','a+')
tagged = open('tagged.txt','a+')
with ExifTool() as exif:
	for i, path in enumerate(paths):
		print(i+1,path, flush = True, end = ' ')
		subject = exif.execute('-Subject', str(path))
		firsttag = exif.execute('-Subject', str(path), '-listItem','0')
		if len(subject) == 0 or ',' in firsttag:
			id = re.search('wallhaven-(.*).(jpg|png)', str(path)).group(1)
			limit = 0
			while True:
				try:
					if str(path) in invalids:
						raise wh.exceptions.PageNotFoundError
					if str(path) in taggeds:
						break
					data = wallhaven.get_wallpaper_info(wallpaper_id=id)
					tags = data['tags']
					args = []
					finaltag = ""
					for j, tag in enumerate(tags):
						args.append('-Subject='+tag['name'])
						finaltag += tag['name']
						if j < len(tags) - 1:
							finaltag += ', '
					args.append('-overwrite_original')
					args.append('-P')
					args.append(str(path))					
					tagstr = ""
					for arg in args:
						tagstr += arg+'\n'
					exif.execute(tagstr)
					if limit > 0:
						print('\t',limit,end=' ')
					print('-', finaltag)
					break
				except wh.exceptions.PageNotFoundError:
					limit = -1
					invalid.write(str(path)+'\n')
					print('<> Invalid ID, Skipping')
					break
				except wh.exceptions.RequestLimitError:
					limit += 1
					if limit == 1:
						print('... Request Limit Error, retrying')
					if limit > 10:
						print("Request Limit Error too many times(EXITING)",limit)
						exit()
					time.sleep(1)
				# except UnicodeEncodeError:
				# 	print('!! UnicodeEncodeError')
				# 	break
		else:
			print('=', re.search('.*: (.*)',str(subject)).group(1))
			tagged.write(str(path)+' = '+re.search('.*: (.*)',str(subject)).group(1))
print('done')
