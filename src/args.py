from argparse import ArgumentParser
from pathlib import Path

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
    required=True,
    metavar='name',
    type=str,
    default='CVehicle',
    help='The class name in the IDB.'
)
parser.add_argument(
    '--pdtypes',
    action='store_true',
    help='Function parameter types will be extracted from the demangled name rather than the function prototype.'
)

# TODO
# parser.add_argument(
#     '--rcalls',
#     action='store_true',
#     help='Adds <className>_Reversed wrappers for virtual functions.'
# ) 
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

if not args.db_path.exists():
    raise NotADirectoryError('Plugin SDK export path invalid (-i). Run the IDA plugin-sdk exporter plugin. (IDA: Edit -> Plugins)')
    
args.output.mkdir(parents=True, exist_ok=True)  # Make sure dir exists

DATABASE_PATH = args.db_path
OUTPUT_PATH = args.output
ARG_TYPES_FROM_DEMANGLED_NAME = True
