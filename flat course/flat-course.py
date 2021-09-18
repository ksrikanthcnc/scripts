import sys
import os,re,shutil
if len(sys.argv) < 3:
    print('<py> <path> <regex>')
    input('Enter to exit')
    exit()
rootdir = sys.argv[1]
regex = f'(?:{sys.argv[2]})'
# rootdir = 'E:\Courses\Complete Git Guide- Understand and master Git and GitHub'
# regex = '(?:\. )'
flatpath = f'{rootdir}\\flat'
if not os.path.exists(flatpath):
    print(f'Creating {flatpath}')
    os.makedirs(flatpath)
for root, dirs, files in os.walk(rootdir):
    if root in [rootdir,flatpath]:
        continue
    print(f'\t\t{root}')
    # for dir in dirs:
    #     print(dir)
    path = root.replace(f'{rootdir}\\',"")
    matches = [int(match) for match in re.findall(f'(\d+){regex}',path)]
    pre = '_'.join([f'{n:02}' for n in matches])
    for file in files:
        if any([ext in file for ext in ['mp4','avi','srt','vtt']]):
            From = f'{root}\\{file}'
            path = From.replace(f'{rootdir}',"")
            matches = [int(match) for match in re.findall('(\d+)(?:. )',path)]
            pre = '_'.join([f'{n:02}' for n in matches])
            To = f'{flatpath}\\{pre}_{file}'
            if not os.path.exists(To):
                print(f'{From} -> {To}')
                shutil.copy(From,To)
            else:
                print(f'{To} exists in target already')
            # exit()
        else:
            print(f'Skipping unrelated [{file}]')
input('Done, enter to exit')
