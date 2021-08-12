from argparse import ArgumentParser
from pathlib import Path

import jinja2 as j2

import CSVFunctionExtract
import CSVStaticVariableExtract
import JSONStructExtract
from models.Function import FunctionType

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
    '--rcalls',
    action='store_true',
    help='Adds <className>_Reversed wrappers for virtual functions.'
)
parser.add_argument(
    '--pdtypes',
    action='store_true',
    help='Function parameter types will be extracted from the demangled name rather than the function prototype.'
)
parser.add_argument(
    '--norwv3d',
    action='store_true',
    default=False,
    help='Convert RwV3d to CVector, and RwV3d to const CVector&'
)
parser.add_argument(
    '--noptrvector',
    action='store_true',
    default=False,
    help='Convert CVector* to const CVector&'
)
parser.add_argument(
    '--indent',
    action='store',
    default=' ' * 4,
    help='Indentation for the code. By default 4 spaces'
)
args = parser.parse_args()

args.output.mkdir(parents=True, exist_ok=True)  # Make sure dir exists
if not args.db_path.exists():
    raise NotADirectoryError('Plugin SDK export path invalid (-i). Run the IDA plugin-sdk exporter plugin. (IDA: Edit -> Plugins)')

j2env = j2.Environment(
    loader=j2.FileSystemLoader(searchpath='templates/'),
    autoescape=None,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True
)


# file - A path to the output file relative to `args.output`
def render_and_write_template(class_name, template_name: str, file: str, **kwargs):
    file_path = args.output / file

    with file_path.open('w', encoding='UTF-8') as file:
        template = j2env.get_template(template_name)
        data = template.render(class_name=class_name, **kwargs)
        file.write(data)


def process_one(klass: str, database: str, pdtypes):
    functions = CSVFunctionExtract.extract(klass, database, pdtypes)
    static_vars = CSVStaticVariableExtract.extract(klass, database)
    json_struct = JSONStructExtract.extract(klass, database)

    def _render_and_write_template(template_name: str, file_name: str):
        render_and_write_template(
            klass,
            template_name,
            file_name,
            **functions,
            static_vars=static_vars,
            FunctionType=FunctionType,
            **json_struct
        )

    _render_and_write_template('source.jinja2', f'{klass}.cpp')
    _render_and_write_template('header.jinja2', f'{klass}.h')


def run():
    process_one(args.class_name, args.db_path, args.pdtypes)


if __name__ == '__main__':
    run()
