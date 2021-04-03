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

invalids = []
invalid = open('invalid.txt','r+')
for line in invalid.readlines():
	invalids.append(line[:-1])
invalid.close()

foldereds = []
foldered = open('foldered.txt','r+')
for line in foldered.readlines():
	foldereds.append(line[:-1])
foldered.close()

import wallhaven as wh
from wallhaven import Wallhaven
import re
import json
import os
from shutil import copyfile
import subprocess
import time
apif = open('whapi.txt')
api=apif.readline()
wallhaven = Wallhaven(api)
# wallhaven.REQUEST_TIMEOUT = 0
invalid = open('invalid.txt','a+')
foldered = open('foldered.txt','a+')

data ={'purity':'init'}
for i, path in enumerate(paths):
	print(len(paths)-i, end='--',flush = True)
	id = re.search('wallhaven-(.*).(jpg|png)', str(path)).group(1)
	limit = 0
	while True:
		try:
			if str(path) in invalids:
				raise wh.exceptions.PageNotFoundError
			if str(path) in foldereds:
				raise FileExistsError
			data = wallhaven.get_wallpaper_info(wallpaper_id=id)
			if limit > 0:
				print('\t',limit,end=' ')
			# foldered.write(str(path)+'\n')
			# foldered.flush()
			dest = "{0}\\foldered\{1}\{2}".format(os.path.dirname(path),data['purity'],os.path.basename(path))
			# dest = "{0}\{1}\{2}".format(r'C:\Users\Kalyanam\Pictures\New folder\\',data['purity'],os.path.basename(path))

			print(data['purity'], dest)
			if not os.path.exists(os.path.dirname(dest)):
				os.makedirs(os.path.dirname(dest))
			os.rename(path,dest)
			# copyfile(path,dest)
			break
		except wh.exceptions.PageNotFoundError:
			limit = -1
			invalid.write(str(path)+'\n')
			print('<> Invalid ID, Skipping')
			data['purity'] = 'invalid'
			dest = "{0}\\foldered\{1}\{2}".format(os.path.dirname(path),data['purity'],os.path.basename(path))
			print(data['purity'], dest)
			if not os.path.exists(os.path.dirname(dest)):
				os.makedirs(os.path.dirname(dest))
			os.rename(path,dest)
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
		except wh.exceptions.RequestLimitError:
			limit += 1
			if limit == 1:
				print('... Request Limit Error, retrying')
			if limit > 10:
				print("Request Limit Error too many times(EXITING)",limit)
				exit()
			time.sleep(1)
		except FileNotFoundError:
			print('Skipping, file not found')
			break
		except Exception as e:
			print("Exception [{0}]:[{1!r}]".format(type(e).__name__,e.args))
			break
print('done')
