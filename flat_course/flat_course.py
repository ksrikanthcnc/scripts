import sys
import os,re,shutil
dryrun = False
if len(sys.argv) < 2:
    print('<py> <path> [<regex_num[(num)<regex_num(separator)>]>]')
    sys.argv.append(input('enter path'))
regex_num = f'(?:\\\)(\d+)'
regex_file = f'(?:.*)(?:\\\)(?:\d+)(.*)'
rootdir = sys.argv[1]
flatpath = f'{rootdir}\\flat'
if not os.path.exists(flatpath):
    print(f'Creating {flatpath}')
    os.makedirs(flatpath)
for root, dirs, files in os.walk(rootdir):
    if root in [rootdir,flatpath]:
        continue
    print(f'{root}')
    # for dir in dirs:
    #     print(dir)
    path = root.replace(f'{rootdir}\\',"")
    # matches = [int(match) for match in re.findall(regex_num,path)]
    # pre = '_'.join([f'{n:02}' for n in matches])
    for file in files:
        if any([ext in file for ext in ['mp4','avi','srt','vtt']]):
            From = f'{root}\\{file}'
            path = From.replace(f'{rootdir}',"")
            matches = [int(match) for match in re.findall(regex_num,path)]
            file = [match for match in re.findall(regex_file,path)][0]
            pre = '_'.join([f'{n:02}' for n in matches])
            To = f'{flatpath}\\{pre}{file}'
            if not os.path.exists(To):
                f = From.replace(f'{rootdir}',"")
                t = To.replace(f'{rootdir}',"")
                print(f'\t{f} -> {t}')
                if dryrun:
                    pass
                else:
                    shutil.copy(From,To)
            else:
                print(f'{To} exists in target already')
        else:
            # print(f'Skipping unrelated [{file}]', end='\r')
            pass
print('')
input('Done, enter to exit')
