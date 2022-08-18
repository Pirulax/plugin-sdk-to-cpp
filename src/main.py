from pathlib import Path
import os
from cls import Class

# The program is meant to be run from the root dir (eg.: Where LICENSE is)
# but the working directory should actually be where this file is
# so change it
# Also this must be before `args` import, because it has to read a file relative to the actual cwd
if Path.cwd().name != 'src':
    os.chdir('src/')

import args


if __name__ == '__main__':
    def process_one(name : str):
        Class.from_file(name).render_to_file()
    
    if args.CLASSES_TO_PROCESS is not None:
        for cls_name in args.CLASSES_TO_PROCESS:
            print(f"Processing {cls_name}...")
            process_one(cls_name)
    else:
        process_one(args.args.class_name)
