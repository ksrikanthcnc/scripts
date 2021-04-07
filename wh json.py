import sys
import wallhaven as wh
from wallhaven import Wallhaven
import re
import json
import os
import time
from pathlib import Path

if len(sys.argv) > 1:
	rootdirs = sys.argv[1:]
	print('Using paths from args passed')
else:
	rootdirs = [
	r'C:\Users\Kalyanam\Pictures\latest',
	r'C:\Users\Kalyanam\Pictures\Wallpapers',
	# r'C:\Users\Kalyanam\Pictures\latest\Android WallHaven',
	# r'C:\Users\Kalyanam\Pictures\latest\Ubuntu'
	]

paths = []
for rootdir in rootdirs:
    # rglob for recursive
	for path in Path(rootdir).rglob('wallhaven*.*'):
		paths.append(path)
paths.sort()

# fetched = []
ids = []
with open('jsons.txt','r+') as file:
	for line in file.readlines():
		ids.append(json.loads(line[:-1])['id'])
		# fetched.append(line[:-1])

apif = open('../whapi.txt')
api=apif.readline()
wallhaven = Wallhaven(api)
wallhaven.REQUEST_TIMEOUT = 0
jsonsfile = open('jsons.txt','a+')

for i, path in enumerate(paths):
	print(len(paths)-i, end='--',flush = True)
	#file = re.search('wallhaven-(.*).(jpg|png)', str(path))
	file = re.search('wallhaven-(.*)\.(.*)', str(path))
	id = file.group(1)
	ext = file.group(2)
	#print(rf'[{ext}]',end='-')
	if ext != 'png' and ext != 'jpg':
		print(str(path))
		exit()
	limit = 0
	while True:
		try:
			if id in ids:
				print(id, 'Already fetched')
				break
			data = wallhaven.get_wallpaper_info(wallpaper_id=id)
			if limit > 0:
				print('\t',limit,end=' ')
			print(data['id'])
			data=json.dumps(data)+'\n'
			jsonsfile.write(data)
			break
		except wh.exceptions.PageNotFoundError:
			data = json.dumps({"id":id,"invalid":"true"})
			jsonsfile.write(data+'\n')
			print(rf'<{id}> Invalid ID, Skipping')
			break
		except wh.exceptions.RequestLimitError:
			limit += 1
			if limit == 1:
				print('... Request Limit Error, retrying')
			if limit > 10:
				print("Request Limit Error too many times(EXITING)",limit)
				exit()
			time.sleep(limit)
		except Exception as e:
			print("Exception [{0}]:[{1!r}]".format(type(e).__name__,e.args))
			exit()
	jsonsfile.flush()
print('done')
