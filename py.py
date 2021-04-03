import os
shpath = r'C:\Users\Kalyanam\Pictures\WPs'

for filename in os.listdir(shpath):
    file_path = os.path.join(shpath, filename)

    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))
