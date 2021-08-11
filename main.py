from pathlib import Path
from argparse import ArgumentParser

parser = ArgumentParser(description='IDA .h and .cpp wrapper file generator.')
parser.add_argument('-i', required=True, metavar='path', type=Path,
                    help='The path to IDA generated database using plugin-sdk tool.')
parser.add_argument('-o', metavar='path', type=Path, default='output/',
                    help='Output folder path.')
parser.add_argument('-iclass', required=True, metavar='name', type=str,
                    help='The class name in the IDB.')
""" parser.add_argument('--rcalls', action='store_true', 
                    help='Adds <className>_Reversed wrappers for virtual functions.') """
parser.add_argument('--pdtypes', action='store_true', 
                    help='Function parameter types will be extracted from the demangled name rather than the function prototype.')
""" parser.add_argument('--norwv3d', action='store_true', default=False,
                    help='Convert RwV3d to CVector, and RwV3d to const CVector&')
parser.add_argument('--noptrvector', action='store_true', default=False,
                    help='Convert CVector* to const CVector&') """
args = parser.parse_args()
class_name = args.iclass

args.o.mkdir(parents=True, exist_ok=True) # Make sure dir exists

import jinja2 as j2
import CSVFunctionExtract
from CSVFunctionExtract import FunctionType
import CSVStaticVariableExtract
import JSONStructExtract

j2env = j2.Environment(
    loader=j2.FileSystemLoader(searchpath='templates/'),
    autoescape=None,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True
)

j2env.globals |= JSONStructExtract.Extract(class_name, args.i) | CSVFunctionExtract.Extract(class_name, args.i, args.pdtypes) | {
    'FunctionType': FunctionType,
    'static_vars': CSVStaticVariableExtract.Extract(class_name, args.i),
    'class_name': class_name
} 

def render_and_write_template(type : str):
    with (args.o / f'{class_name}.{type}').open('w', encoding='UTF-8') as f:
        f.write(j2env.get_template(type + '.jinja2').render())
render_and_write_template('cpp')
render_and_write_template('h')
