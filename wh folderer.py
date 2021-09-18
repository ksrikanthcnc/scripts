import subprocess
import os
import json
import sys
import re
import json
import os
from shutil import copyfile,move
import subprocess
from pathlib import Path

if len(sys.argv) > 1:
	rootdirs = sys.argv[1:]
	print('Using paths from args passed')
else:
	rootdirs = [
	#r'C:\Users\Kalyanam\Pictures\latest',
	#r'C:\Users\Kalyanam\Pictures\latest\Android WallHaven',
	#r'C:\Users\Kalyanam\Pictures\latest\Ubuntu'
	]

paths = []
for rootdir in rootdirs:
	print(rootdir)
    # rglob for recursive
	for path in Path(rootdir).glob('wallhaven*.*'):
		paths.append(path)
paths.sort()

jsons = {}
with open('files\jsons.txt','r+') as file:
	for line in file.readlines():
		jsob = json.loads(line[:-1])
		jsons[jsob['id']] = jsob

folder = ""
dest = ''
for i, path in enumerate(paths):
	id = re.search('wallhaven-(.*).(jpg|png)', str(path)).group(1)
	print(len(paths)-i,id, end='--',flush = True)
	try:
		folder = jsons[id]['purity']
	except KeyError:
		if id in jsons:
			folder = 'invalid'
		else:
			print('Run wh jsons.py to update jsons')
			continue
	except Exception as e:
		# print("Exception [{0}]:[{1!r}]".format(type(e).__name__,e.args))
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(rf"{type(e).__name__}@{fname}:{exc_tb.tb_lineno}")

	print(folder,end = '')
	dest = "{0}\\foldered\{1}\{2}".format(os.path.dirname(path),folder,os.path.basename(path))
	if not os.path.exists(os.path.dirname(dest)):
		os.makedirs(os.path.dirname(dest))
	try:
		os.rename(path,dest)
		# copyfile(path,dest)
	except FileExistsError:
		print('(repeated)',end='')
		folder = 'repeated'
		dest = "{0}\\foldered\{1}\{2}".format(os.path.dirname(path),folder,os.path.basename(path))
		if not os.path.exists(os.path.dirname(dest)):
			os.makedirs(os.path.dirname(dest))
		move(path,dest)
	except FileNotFoundError:
		print('(Skipping, file not found)')
	print('')
print('done')
