import subprocess
import os
import json
from pathlib import Path
import sys
import re

class ExifTool(object):
    sentinel = "{ready}\r\n"
    def __init__(self, executable=r'D:\MyProgs\exiftool.exe'):
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

if len(sys.argv) > 1:
	rootdirs = sys.argv[1:]
	print('Using paths from args passed')
else:
	path = input('Enter path')
	rootdirs = [
#		r'E:\Drive\Wallpapers'
	]
	rootdirs.append(path)

paths = {}
for rootdir in rootdirs:
	for path in Path(rootdir).rglob('wallhaven*.*'):
		id = re.search('wallhaven-(.*).(jpg|png)', str(path)).group(1)
		paths[id] = path

data = {}
with open(r'..\files\jsons.txt','r+') as file:
	for line in file.readlines():
		jsob = json.loads(line[:-1])
		data[jsob['id']]=jsob

count = 0
notag = open('notag.txt','w')
with ExifTool() as exif:
	for i,id in enumerate(paths):
		print(len(paths)-i,paths[id],"                                                          ",end='\r')
		if id not in data:
			print(id,'Run wh json.py and update jsons.txt')
			continue
		if 'invalid' in data[id]:
			continue
		if data[id]['tags'] == []:
			print(id,'No Tag')
			notag.write(f'{data[id]}\n')
			continue
		subject = exif.execute('-Subject\n-m', str(paths[id]))
		if subject == '':
			print(i+1, paths[id], flush = True, end = '--')
			tags = data[id]['tags']
			args = []
			finaltag = ""
			for j, tag in enumerate(tags):
				args.append('-Subject='+tag['name'])
				finaltag += tag['name']+','
			print(finaltag,end='')
#			args.append('-overwrite_original')
			args.append('-overwrite_original_in_place')
			args.append('-P')
			args.append('-m')
			args.append(str(paths[id]))
			tagstr = ""
			for arg in args:
				tagstr += arg+'\n'
			exif.execute(tagstr)
			count+=1
			print('')
print(count)
input('done;enter to exit')
