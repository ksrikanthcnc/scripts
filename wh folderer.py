import subprocess
import os
import json
import sys

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
    # rglob for recursive
	for path in Path(rootdir).glob('wallhaven*.*'):
		paths.append(path)
paths.sort()

import re
import json
import os
from shutil import copyfile
import subprocess
jsons = {}
with open('jsons.txt','r+') as file:
	for line in file.readlines():
		jsob = json.loads(line[:-1])
		jsons[jsob['id']] = jsob

jsons = open('jsons.txt','r')

data ={'purity':'init'}
for i, path in enumerate(paths):
	print(len(paths)-i, end='--',flush = True)
	id = re.search('wallhaven-(.*).(jpg|png)', str(path)).group(1)
	try:
		data = jsons[id]
		dest = "{0}\\foldered\{1}\{2}".format(os.path.dirname(path),data['purity'],os.path.basename(path))
		print(data['purity'], dest)
		if not os.path.exists(os.path.dirname(dest)):
			os.makedirs(os.path.dirname(dest))
		os.rename(path,dest)
		# copyfile(path,dest)
		break
	except FileExistsError:
		print('Skipping, file already exists')
		data['purity'] = 'repeated'
		dest = "{0}\\foldered\{1}\{2}".format(os.path.dirname(path),data['purity'],os.path.basename(path))
		print(data['purity'], dest)
		if not os.path.exists(os.path.dirname(dest)):
			os.makedirs(os.path.dirname(dest))
		try:
			os.rename(path,dest)
		except FileExistsError:
			pass
		break
	except FileNotFoundError:
		print('Skipping, file not found')
		break
	except Exception as e:
		print("Exception [{0}]:[{1!r}]".format(type(e).__name__,e.args))
		break
print('done')
