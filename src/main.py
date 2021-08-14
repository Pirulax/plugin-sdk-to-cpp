from pathlib import Path
from args import args
import os
import PerClassProcessor

# The program is meant to be run from the root dir (eg.: Where LICENSE is)
# but the working directory should actually be where this file is
# so change it
if Path.cwd().name != 'src':
    os.chdir('src/')

if __name__ == '__main__':
    PerClassProcessor.process(args.class_name)
