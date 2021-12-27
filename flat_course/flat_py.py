from shutil import copy
import sys
import os,re
if len(sys.argv) < 2:
    print('<py> <path> [<regex_num[(num)<regex_num(separator)>]>]')
    # sys.argv.append(input('enter path'))
    sys.argv.append(r'E:\Courses\0.Spark and Python for Big Data with PySpark')
regex_num = f'(?:\\\)(\d+)'
regex_file = f'(?:.*)(?:\\\)(?:\d+)(.*)'
regex_dir = f'(?:.*)(?:\\\)(?:\d+)(.*)'
rootdir = sys.argv[1]
flatpath = f'{rootdir}\\flat'

def list_dict(ls,d,file):
    if ls == [] or isinstance(d,str):
        return file
    if not any(_ in d for _ in ls):
        dd = {}
        d[str(ls)] = list_dict(ls[1:],dd,file)
    else:
        d[str(ls)] = list_dict(ls[1:],d[ls],file)
    return d

d = {}
for root, dirs, files in os.walk(rootdir):
    if root in [flatpath,rf'{rootdir}\q']:
        continue
    if rf'{rootdir}\q' in root:
        continue
    path = root.replace(f'{rootdir}\\',"")
    for dir in dirs:
        From = f'{root}\\{dir}'
        path = From.replace(f'{rootdir}',"")
        if path != r'\flat' and path != r'\q':
            matches = [int(match) for match in re.findall(regex_num,path)]
            file = [match for match in re.findall(regex_file,path)][0]
            pre = '_'.join([f'{n:02}' for n in matches])
            d = list_dict(matches,d,file)
            # print(matches,file)
    for file in files:
        if any([ext in file for ext in ['mp4','avi']]):
            From = f'{root}\\{file}'
            path = From.replace(f'{rootdir}',"")
            matches = [int(match) for match in re.findall(regex_num,path)]
            file = [match for match in re.findall(regex_file,path)][0]
            pre = '_'.join([f'{n:02}' for n in matches])
            d = list_dict(matches,d,file)
            # print(matches,file)

tabs = 0
def print_dict(d):
    global tabs
    tabs += 1
    if isinstance(d,str):
        for _ in range(tabs):print('\t',end='')
        print(f'# {d}')
    else:
        for i in sorted(list(d.keys())):
            print_dict(d[i])
    tabs -= 1

print_dict(d)

print('')
# input('Done, enter to exit')