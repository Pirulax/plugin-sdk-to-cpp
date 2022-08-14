from pathlib import Path
import os
import PerClassProcessor

# The program is meant to be run from the root dir (eg.: Where LICENSE is)
# but the working directory should actually be where this file is
# so change it
# Also this must be before `args` import, because it has to read a file relative to the actual cwd
if Path.cwd().name != 'src':
    os.chdir('src/')

import args


if __name__ == '__main__':
    if args.CLASSES_TO_PROCESS:
        for cls_name in args.CLASSES_TO_PROCESS:
            print(f"Processing {cls_name}...")
            PerClassProcessor.process(cls_name)
    else:
        PerClassProcessor.process(args.args.class_name)
