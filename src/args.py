from argparse import ArgumentParser
from pathlib import Path
import os
import pandas
from models.CallingConvention import CallingConvention

parser = ArgumentParser(description='IDA .h and .cpp wrapper file generator.')
parser.add_argument(
    '--db-path',
    required=True,
    metavar='path',
    type=Path,
    help='The path to IDA generated database using plugin-sdk tool.'
)
parser.add_argument(
    '--output',
    metavar='path',
    type=Path,
    default='../output/',
    help='Output folder path.'
)
parser.add_argument(
    '--class-name',
    required=False,
    metavar='class_name',
    type=str,
    help='The class name in the IDB.'
)
parser.add_argument(
    '--classes-to-process',
    required=False,
    metavar='classes_to_process',
    type=str,
    help='The file containing the list of classes to process, in csv format (columns): class_name'
)
parser.add_argument(
    '--pdtypes',
    action='store_true',
    help='Function parameter types will be extracted from the demangled name rather than the function prototype.'
)
parser.add_argument(
    '--assumed-cc',
    nargs='?',
    const='cdecl',
    type=CallingConvention,
    help='Assume the given calling convention by default for functions whose CC isn`t valid. If this argument is given without value it is defaulted to cdecl'
)
parser.add_argument(
    '--category',
    default="",
    type=str,
    help='The category of the class(es) to process. If using batch-process this servers as a default in case it`s not specified in the classes-to-process file'
)
parser.add_argument(
    '--debug',
    action='store_true',
    default=False,
    help='Enable debug mode'
)
parser.add_argument(
    '--dump-prot',
    action='store_true',
    default=False,
    help='Dump function prototypes'
)
parser.add_argument(
    '--use-static-inline',
    action='store_true',
    default=False,
    help='Define variables in header using C++17 `static inline`'
)
parser.add_argument(
    '--wrap-virtuals',
    action='store_true',
    help='Add `_Reversed` wrappers for virtual functions.'
)
parser.add_argument(
    '--print-vmt-idx',
    action='store_true',
    help='Print VMT index for virtual functions in the header'
) 
parser.add_argument(
    '--print-vmt-info',
    action='store_true',
    help='Whenever to print VMT (address and size) in the header'
)
# TODO
# parser.add_argument(
#     '--norwv3d',
#     action='store_true',
#     default=False,
#     help='Convert RwV3d to CVector, and RwV3d to const CVector&'
# )
# parser.add_argument(
#     '--noptrvector',
#     action='store_true',
#     default=False,
#     help='Convert CVector* to const CVector&'
# )
# parser.add_argument(
#     '--indent',
#     action='store',
#     default=' ' * 4,
#     help='Indentation for the code. By default 4 spaces'
# )
args = parser.parse_args()

if not args.class_name and not args.classes_to_process:
    raise ValueError('You must specify either --class-name or --classes-to-process')

if args.classes_to_process:
    with open(args.classes_to_process, 'r') as f:
        CLASSES_TO_PROCESS = pandas.read_csv(f)["class_name"].values
else:
    CLASSES_TO_PROCESS = None

fix_path = lambda p: Path(os.path.expandvars(os.path.expanduser(p)))

WRAP_VIRTUALS : bool = args.wrap_virtuals
DATABASE_PATH : Path = fix_path(args.db_path)
print(f"{DATABASE_PATH=!r}")
OUTPUT_PATH : Path = fix_path(args.output)
ARG_TYPES_FROM_DEMANGLED_NAME = True
ASSUMED_CC : CallingConvention = args.assumed_cc
DEBUG_MODE : bool = args.debug
DUMP_PROTOTYPES : bool = args.dump_prot
USE_STATIC_INLINE : bool = args.use_static_inline
CATEGORY : str = args.category
PRINT_VMT_IDX : bool = args.print_vmt_idx
PRINT_VMT_INFO : bool = args.print_vmt_info

# Checking this here after it has been fixed
if not DATABASE_PATH.exists():
    raise NotADirectoryError('Plugin SDK export path invalid (-i). Run the IDA plugin-sdk exporter plugin. (IDA: Edit -> Plugins)')

OUTPUT_PATH.mkdir(parents=True, exist_ok=True)  # Make sure dir exists
