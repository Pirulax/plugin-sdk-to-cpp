import re
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from pandas import DataFrame, Series, read_csv
from pandas.core.reshape.concat import concat
from typing import *

# Extract function name from DemangledName column
name_re = re.compile(r'::(~?\w+)\(*?')
def ExtractFunctionFromDemangledName(demangledName : str):
    return name_re.search(demangledName).group(1)

# Replace stupid typenames with their normal counterparts
type_replacements = [
    (r'\bunsigned __int8\b', 'uint8_t'),
    (r'\bunsigned __int16\b', 'uint16_t'),
    (r'\bunsigned __int32\b', 'uint32_t'),
    (r'\b__int8\b', 'int8_t'),
    (r'\b__int16\b', 'int16_t'),
    (r'\b__int32\b', 'int32_t'),
    (r'\b_BYTE\b', 'uint8_t'),
    (r'\bword\b', 'int16_t'),
    (r'\b_WORD\b', 'int16_t'),
    (r'\bWORD\b', 'int16_t'),
    (r'\bsigned int\b', 'int32_t'),
    (r'\bunsigned int\b', 'uint32_t'),
    (r'\bint\b', 'int32_t'),
    (r'\bdword\b', 'int32_t'),
    (r'\b_DWORD\b', 'int32_t',),
    (r'\bstruct\b', ''),
    (r'\b_BOOL1\b', 'bool'),
    (r'\buchar\b', 'uint8_t'),
    (r'\s+\*?', '*') # Fix space between type and * for pointers (Eg.: Foo * => Foo*)
]
type_replacements = [(re.compile(regex), repl) for regex, repl in type_replacements] # Compile all regexes
def NormalizeType(text : str):
    if text == "char":
        return "int8_t"
    for regex, repl in type_replacements:
        text = regex.sub(repl, text)
    return text
    
# Drop type and argument for `this` in case this function is a class method
def MaybePopThisFromArray(array, cc):
    if array and cc in ('thiscall', 'fastcall'):
        array.pop(0)
    return array

# Extract parameter types from demangled name
args_capture_re = re.compile(r'\((.+?)\)')
args_re = re.compile(r'(\w+\s*\*?\s*?(?<![,\)]))')
def ExtractParamTypes(paramTypes : str, cc : str, demangledName : str, fromDemangled : bool):
    if fromDemangled:
        argsCapture = args_capture_re.search(demangledName)
        if argsCapture: # Fails if demangled name doesn't contain types
            # No need to pop `this` as its never in the demangled name
            # Also, don't append the type if it's `void` (void* though is accepted)
            return [NormalizeType(v) for v in args_re.findall(argsCapture.group(0)) if v != 'void'] 
    if paramTypes and paramTypes != 'void': # Skip empty strings, as they produce ['']
        return MaybePopThisFromArray([NormalizeType(t) for t in paramTypes.split('~') if t], cc)
    return []

def ExtractParamNames(paramNames : str, cc : str):
    if paramNames:
        return MaybePopThisFromArray(paramNames.split('~'), cc)
    return []

from enum import Enum
class FunctionType(Enum):
    REGULAR      = 0
    VIRTUAL      = 1
    CTOR         = 2
    DTOR         = 3
    DTOR_VIRTUAL = 4

@dataclass
class Function:
    cls : str                       # Class this function belongs to
    full_name : str
    name : str
    address : str
    ret_type : str                  # Ctors and dtors have a retun type equal to the type of `this`
    vt_index : np.int16
    cc : str                        # Calling convention
    args : List[Tuple[str, str]]    # (type, name) list of function arguments
    is_static : bool = False        # If the function is static
    type : FunctionType = None
    plugin_call_src : str = None    # C++ source code for the plugin call stuff
    param_name_types : str = None
    #plugin_call_template : str     # Eg.: "bool, 0xBEEF, CFoo*, bool"
    #plugin_call_args : str         # Eg.: "this, bValue" (For the above template)
    #plugin_function : str          # Eg.: "StdCall", "Call", "CallMethodAndReturn"

    def __post_init__(self):
        self.is_static = self.cc in ('cdecl', 'stdcall')
        self.plugin_call_src = PluginSDKCall(self)
        self.param_name_types = ', '.join([' '.join(a) for a in self.args])
        print(self.param_name_types)
        if f'{self.cls}::{self.cls}' in self.full_name: # constructor
            self.type = FunctionType.CTOR
            self.ret_type = self.cls + '*'
        elif f'{self.cls}::~{self.cls}' in self.full_name: # destructor
            self.type = FunctionType.DTOR if self.vt_index == -1 else FunctionType.DTOR_VIRTUAL
            self.ret_type = self.cls + '*'
        else:
            self.type = FunctionType.REGULAR if self.vt_index == -1 else FunctionType.VIRTUAL

def PluginSDKCall(fn : Function):
    ccToPluginFn = {
        'thiscall': "CallMethod",
        'fastcall': "FastCall",
        'cdecl': "Call",
        'stdcall' :"Call"
    }   
    template = []
    args = []
    pluginFn = ccToPluginFn[fn.cc]
    if fn.ret_type != "void":
        pluginFn += "AndReturn"
        template.append(fn.ret_type)
    template.append(fn.address)
    if fn.cc in ('thiscall', 'fastcall'): # Check is method call
        template.append(fn.cls + '*') 
        args.append("this")
    template += [t for t, n in fn.args]
    args += [n for t, n in fn.args]
    return f'{"" if fn.ret_type == "void" else "return "}plugin::{pluginFn}<{", ".join(template)}>({", ".join(args)})'

# Returns a tuple of (Non-Virtual, and Virtual[Sorted by vmt index]) functions belonging to this class
def Extract(className : str, database : Path, argTypesFromDemangled : bool):
    # Cols used and their respective type
    cols = {
        '10us': str,
        #'Module': str,
        'Name': str,
        'DemangledName': str,
        'Type': str,
        'CC': str,
        'RetType': str,
        'ParamTypes': str,
        'ParamNames': str,
        #'IsConst': bool,
        #'Refs': np.int16,
        #'Comment': str,
        #'Priority': bool,
        'VTIndex': np.int16,
        #'ForceOverloaded': bool
    }
    csv_df = read_csv(database / "plugin-sdk.out.functions.csv", dtype=cols, usecols=cols.keys(), engine='c', sep=',', na_values=[], keep_default_na=False)
    csv_df = csv_df[csv_df['DemangledName'].str.startswith(className)] # Only class members
    csv_df.sort_values(inplace=True, by='VTIndex')
    csv_df.reset_index(inplace=True)
    # Create data that fits our needs, normalize types, etc..
    fn_series = csv_df[['ParamTypes', 'ParamNames', 'CC', 'DemangledName', 'RetType', 'VTIndex', '10us']].apply(lambda s: Function(
        cls=className,
        full_name=s[3],
        name=ExtractFunctionFromDemangledName(s[3]),
        address=s[6],
        ret_type=NormalizeType(s[4]),
        vt_index=s[5],
        cc=s[2],
        args=[(t, n) for t, n in zip(ExtractParamTypes(s[0], s[2], s[3], argTypesFromDemangled), ExtractParamNames(s[1], s[2]))]
    ), axis=1) # Apply on each row

    filter_by_type = lambda ts: fn_series.loc[fn_series.apply(lambda f: f.type in ts)].tolist()
    dtor = filter_by_type([FunctionType.DTOR, FunctionType.DTOR_VIRTUAL])
    return {
        'ctors': filter_by_type([FunctionType.CTOR]),
        'dtor': dtor[0] if dtor else None, # There can be only one destructor, so this has to be a single item, not a list
        'virtual_fns': filter_by_type([FunctionType.VIRTUAL]),
        'regular_fns': filter_by_type([FunctionType.REGULAR]),
    }
