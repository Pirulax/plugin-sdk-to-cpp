from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

import numpy as np


class FunctionType(Enum):
    REGULAR      = 0
    VIRTUAL      = 1
    CTOR         = 2
    DTOR         = 3
    DTOR_VIRTUAL = 4


@dataclass
class Function:
    cls: str                        # Class this function belongs to
    full_name: str
    name: str
    address: str
    ret_type: str                   # Ctors and dtors have a retun type equal to the type of `this`
    vt_index: np.int16
    cc: str                         # Calling convention
    args: List[Tuple[str, str]]     # (type, name) list of function arguments
    is_static: bool = False         # If the function is static
    type: FunctionType = None
    plugin_call_src: str = None     # C++ source code for the plugin call stuff
    param_name_types: str = None
    # plugin_call_template: str      # Eg.: "bool, 0xBEEF, CFoo*, bool"
    # plugin_call_args: str          # Eg.: "this, bValue" (For the above template)
    # plugin_function: str           # Eg.: "StdCall", "Call", "CallMethodAndReturn"

    def PluginSDKCall(self):
        # Calling Convention to plugin func
        cc_plugin_func_map = {
            'thiscall': 'CallMethod',
            'fastcall': 'FastCall',
            'cdecl': 'Call',
            'stdcall': 'Call',

            # TODO (Izzotop): Fix that
            '': 'CallX',
            'unknown': 'CallX'
        }
        template = []
        args = []
        plugin_func = cc_plugin_func_map[self.cc]
        if self.ret_type != 'void':
            plugin_func += 'AndReturn'
            template.append(self.ret_type)

        template.append(self.address)
        if self.cc in ('thiscall', 'fastcall'):  # Check is method call
            template.append(self.cls + '*')
            args.append('this')

        template += [t for t, n in self.args]
        args += [n for t, n in self.args]
        return f'{"" if self.ret_type == "void" else "return "}plugin::{plugin_func}<{", ".join(template)}>({", ".join(args)})'

    def __post_init__(self):
        self.is_static = self.cc in ('cdecl', 'stdcall')
        self.plugin_call_src = self.PluginSDKCall()
        self.param_name_types = ', '.join([' '.join(a) for a in self.args])

        # print(self.param_name_types)

        if f'{self.cls}::{self.cls}' in self.full_name: # constructor
            self.type = FunctionType.CTOR
            self.ret_type = self.cls + '*'
        elif f'{self.cls}::~{self.cls}' in self.full_name: # destructor
            self.type = FunctionType.DTOR if self.vt_index == -1 else FunctionType.DTOR_VIRTUAL
            self.ret_type = self.cls + '*'
        else:
            self.type = FunctionType.REGULAR if self.vt_index == -1 else FunctionType.VIRTUAL
