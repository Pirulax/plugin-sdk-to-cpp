import json
from pathlib import Path
from args import OUTPUT_PATH
import jinja2 as j2
import CSVFunctionExtract
import CSVStaticVariableExtract
import JSONStructExtract
import args
from models.Variable import Variable
from models.Function import Function, FunctionType

BUILTIN_TYPES = {'bool', 'char', 'int', 'float', 'double', 'long', 'long long', 'short', 'unsigned char', 'unsigned int', 'unsigned long', 'unsigned long long', 'unsigned short', 'void'}

def is_type_builtin(typ : str) -> bool:
    return not typ.startswith("C") or typ in BUILTIN_TYPES

class Class:
    def __init__(self, name : str, size : str, mem_vars : list[Variable], static_vars : list[Variable], fns : list[Function], vtbl_addr : int, vtbl_size : int):
        self.name = name
        self.size = size
        self.mem_vars = mem_vars
        self.static_vars = static_vars
        self.functions = fns
        self.vtbl_addr = vtbl_addr
        self.vtbl_size = vtbl_size
        self.bases : list[str] = []
        self.types_to_fwd_declare : set[str] = set()
        self.types_to_include : set[str] = set()

        # Variables that begin with baseclass_ are considered base-classes
        for idx, var in enumerate(self.mem_vars):
            if var.namespaceless_name.startswith("baseclass_"):
                self.bases.append(var.type)
                if not is_type_builtin(var.type):
                    self.types_to_include.add(var.type)
                self.mem_vars.pop(idx)

        for var in self.mem_vars:
            if not is_type_builtin(var.type):
                (self.types_to_fwd_declare if var.is_type_pointer else self.types_to_include).add(var.no_extent_type.replace('*', ''))

    def render_to_file(self):
        j2env = j2.Environment(
            loader=j2.FileSystemLoader(searchpath='templates/'),
            autoescape=None,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        j2env.filters.update({
            "removeprefix": str.removeprefix
        })
        j2env.globals.update({
            **self.__dict__,
            **args.__dict__,
            'class_name': self.name,
            'removesuffix': str,
            'FunctionType': FunctionType,
        })

        file_name = self.name.replace("<", "_").replace(">", "_").removeprefix("C")
        for template, out_ext in (('source', 'cpp'), ('header', 'h')):
            with (OUTPUT_PATH / f'{file_name}.{out_ext}').open('w', encoding='UTF-8') as file:
                file.write(j2env.get_template(f'{template}.jinja2').render())

    @classmethod
    def from_file(cls, name : str):
        struct_info = JSONStructExtract.extract(name)
        functions   = CSVFunctionExtract.extract(name)
        static_vars = CSVStaticVariableExtract.extract(name)
        return cls(
            name=name,
            size=struct_info["size"],
            mem_vars=struct_info["variables"],
            static_vars=static_vars,
            fns=functions,
            vtbl_addr=struct_info["vtbl_addr"],
            vtbl_size=struct_info["vtbl_size"],
        )
