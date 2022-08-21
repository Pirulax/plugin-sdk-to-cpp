from enum import Enum
from functools import cache
from typing import List
import numpy as np
import re
from models.CallingConvention import CallingConvention
import ArgsExtract
from args import ASSUMED_CC
from models import Type

name_re = re.compile(r'(?:::|__)(~?\w+)')

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
    cls: str                # Class this function belongs to
    namespaceless_name: str # Name without class prefix
    address: int            # Address in hex form (Eg.: 0xBEEF)
    ret_type: Type          # Return type of this function, ctors and dtors always return the `class type pointer` (eg.: `this`)
    vt_index: np.int16      # Index in VMT
    cc: CallingConvention
    arg_types : List[Type]  # Argument types
    arg_names : List[str]   # Argument names
    type: FunctionType      # Type of the function
    is_overloaded : bool    # Is this function overloaded
    is_hooked : bool        # Whenever the function should be hooked or not

    def __init__(self, class_name : str, address : str, demangled_name : str, cc : str, ret_type : str, arg_types : str, arg_names : str, vt_index : np.int16, is_overloaded : bool, **kwargs):
        self.cls = class_name
        self.namespaceless_name = extract_name_from_demangled(demangled_name)
        self.address = int(address, base=16)
        self.vt_index = vt_index
        
        try:
            self.cc = CallingConvention(cc)
        except ValueError:
            if ASSUMED_CC:
                print(f"Function {self.namespaceless_name}({self.address}) has invalid CC (`{cc}`). Using assumed cc `{ASSUMED_CC}`")
                self.cc = CallingConvention(ASSUMED_CC)
            else:
                print(f"Function {self.namespaceless_name}({self.address}) has invalid CC (`{cc}`). Aborting. Use `--assumed-cc` to default a calling convention. This error can be fixed by going to IDA, pressing Y on the given function, then enter.")
                exit(1)

        self.arg_names, self.arg_types = ArgsExtract.extract(arg_types, arg_names, demangled_name, self.cc)
        self.is_overloaded = is_overloaded

        # Figure out type
        if self.namespaceless_name == self.cls:
            self.type = FunctionType.CTOR
            ret_type = self.cls + '*'
        elif self.namespaceless_name == '~' + self.cls:
            self.type = FunctionType.DTOR if self.vt_index == -1 else FunctionType.DTOR_VIRTUAL
            ret_type = self.cls + '*'
        elif self.cc.is_static:
            self.type = FunctionType.STATIC
        else:
            self.type = FunctionType.METHOD if self.vt_index == -1 else FunctionType.VIRTUAL

        self.ret_type = Type(ret_type)

        # CTORs and DTOR must be hooked
        self.is_hooked = self.type in (FunctionType.CTOR, FunctionType.DTOR, FunctionType.DTOR_VIRTUAL)

    @property
    def address_hex(self):
        """
        Return the function's address in hex form
        """

        return f'0x{self.address:X}'

    @property
    @cache
    def full_name(self):
        """
        Name with class namespace prefix. Eg.: Class::Function
        """

        return f'{self.cls}::{self.namespaceless_name}'

    @property
    @cache
    def param_names(self) -> str:
        """
        :return: Function argument names separated by commas. Eg.: `a, b, c`
        """

        return ', '.join(self.arg_names)

    @property
    @cache
    def param_types(self) -> str:
        """
        :return: Function argument types separated by commas. Eg.: `int, float, char*`
        """

        return ', '.join(str(a) for a in self.arg_types)

    @property
    @cache
    def param_name_types(self) -> str:
        """
        :return: Function arguments and types zipped together, and separated by commas. Eg.: `int a, float b, char* c`
        """

        return ', '.join(f'{a_type} {a_name}' for a_type, a_name in zip(self.arg_types, self.arg_names))

    @property
    def is_virtual(self) -> bool:
        """
        :return: Is the function virtual
        """

        return self.type in (FunctionType.VIRTUAL, FunctionType.DTOR_VIRTUAL)

    @property
    def is_dtor(self) -> bool:
        """
        :return: Is destructor
        """

        return self.type in (FunctionType.DTOR_VIRTUAL, FunctionType.DTOR)

    @property
    def is_ctor(self) -> bool:
        """
        :return: Is constructor
        """

        return self.type == FunctionType.CTOR

    @property
    def is_static(self) -> bool:
        """
        :return: Is static
        """

        return self.cc.is_static

    @property 
    def is_method(self) -> bool:
        """
        :return: Is calling convention of a method's
        """

        return self.cc.is_method

    @property
    @cache
    def plugin_call_src(self):
        """
        C++ source code for the plugin call stuff
        """

        template_args = [] # The template arguments for the plugin:: call
        arg_names = []

        plugin_func = self.cc.plugin_fn
        if self.ret_type != 'void':
            plugin_func += 'AndReturn'
            template_args.append(str(self.ret_type))

        template_args.append(self.address_hex)

        # `this` is never in the args list, so have to add it separately
        if self.cc.is_method:
            template_args.append(self.cls + '*')
            arg_names.append('this')

        template_args += [str(t) for t in self.arg_types]
        arg_names     += self.arg_names
        
        return f'{"" if self.ret_type == "void" else "return "}plugin::{plugin_func}<{", ".join(template_args)}>({", ".join(arg_names)})'

    def __repr__(self) -> str:
        return f'{self.namespaceless_name} @ {self.address}'
