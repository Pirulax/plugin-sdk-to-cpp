from enum import Enum
from type_replacement import normalize_type
from typing import List
import numpy as np
import re
from models.CallingConvention import CallingConvention
import ArgsExtract

name_re = re.compile(r'(?:::|__)(~?\w+)\(')


def extract_name_from_demangled(demangled_name : str):
    name = demangled_name.replace('__', '::')
    return name_re.search(name).group(1)

class FunctionType(Enum):
    METHOD       = 0
    STATIC       = 1
    VIRTUAL      = 2
    CTOR         = 3
    DTOR         = 4
    DTOR_VIRTUAL = 5

class Function:
    cls: str              # Class this function belongs to
    name: str             # Name without class prefix
    address: str          # Address in hex form (Eg.: 0xBEEF)
    ret_type: str         # Ctors and dtors have a return type equal to the type of `this`
    vt_index: np.int16    # Index in VMT
    cc: CallingConvention
    arg_types : List[str] # Argument types
    arg_names : List[str] # Argument names
    type: FunctionType    # Type of the function   
    is_overloaded : bool  # Is this function overloaded 

    def __init__(self, class_name : str, address : str, demangled_name : str, cc : str, ret_type : str, arg_types : str, arg_names : str, vt_index : np.int16, is_overloaded : bool, **kwargs):
        self.cls = class_name
        self.name = extract_name_from_demangled(demangled_name)
        self.address = address
        self.ret_type = normalize_type(ret_type)
        self.vt_index = vt_index
        self.cc = CallingConvention(cc)
        self.arg_names, self.arg_types = ArgsExtract.extract(arg_types, arg_names, demangled_name, self.cc)
        self.is_overloaded = is_overloaded

        # Figure out type
        if self.name == self.cls: 
            self.type = FunctionType.CTOR
            self.ret_type = self.cls + '*'
        elif self.name == '~' + self.cls:
            self.type = FunctionType.DTOR if self.vt_index == -1 else FunctionType.DTOR_VIRTUAL
            self.ret_type = self.cls + '*'
        elif self.cc.is_static:
            self.type = FunctionType.STATIC
        else:
            self.type = FunctionType.METHOD if self.vt_index == -1 else FunctionType.VIRTUAL

    @property
    def full_name(self):
        # Name with class namespace prefix. Eg.: Class::Function
        return f'{self.cls}::{self.name}'

    @property
    def param_names(self) -> str:
        return ', '.join(self.arg_names)

    @property
    def param_types(self) -> str:
        return ', '.join(self.arg_types)

    @property
    def param_name_types(self) -> str:
        return ', '.join([' '.join(a) for a in zip(self.arg_types, self.arg_names)])

    @property
    def is_virtual(self) -> bool:
        return self.type in (FunctionType.VIRTUAL, FunctionType.DTOR_VIRTUAL)

    @property
    def is_dtor(self) -> bool:
        return self.type in (FunctionType.DTOR_VIRTUAL, FunctionType.DTOR)

    @property
    def is_ctor(self) -> bool:
        return self.type == FunctionType.CTOR

    @property
    def is_static(self) -> bool:
        return self.cc.is_static

    @property 
    def is_method(self) -> bool:
        return self.cc.is_method

    @property
    def plugin_call_src(self):
        # C++ source code for the plugin call stuff

        template = []
        args = []
        plugin_func = self.cc.plugin_fn
        if self.ret_type != 'void':
            plugin_func += 'AndReturn'
            template.append(self.ret_type)

        template.append(self.address)
        if self.cc in ('thiscall', 'fastcall'):  # Check is method call
            template.append(self.cls + '*')
            args.append('this')

        template += self.arg_types
        args += self.arg_names
        return f'{"" if self.ret_type == "void" else "return "}plugin::{plugin_func}<{", ".join(template)}>({", ".join(args)})'
