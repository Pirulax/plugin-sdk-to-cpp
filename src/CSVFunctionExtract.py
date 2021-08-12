import re
from pathlib import Path

import numpy as np
from pandas import read_csv

from models.Function import FunctionType, Function

# Extract function name from DemangledName column
name_re = re.compile(r'::(~?\w+)\(*?')


def extract_function_from_demangled_name(demangled_name : str):
    name = demangled_name.replace('__', '::')
    return name_re.search(name).group(1)


# Replace stupid type_names with their normal counterparts
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
    (r'\s+\*?', '*')  # Fix space between type and * for pointers (Eg.: Foo * => Foo*)
]
type_replacements = [(re.compile(regex), repl) for regex, repl in type_replacements]  # Compile all regexes


def normalize_type(text: str):
    if text == 'char':
        return 'int8_t'

    for regex, repl in type_replacements:
        text = regex.sub(repl, text)

    return text


# Drop type and argument for `this` in case this function is a class method
def maybe_pop_this_from_array(array, cc):
    if array and cc in ('thiscall', 'fastcall'):
        array.pop(0)

    return array


args_capture_re = re.compile(r'\((.+?)\)')
args_re = re.compile(r'(\w+\s*\*?\s*?(?<![,\)]))')


# Extract parameter types from demangled name
def extract_param_types(param_types: str, cc: str, demangled_name: str, from_demangled: bool):
    if from_demangled:
        args_capture = args_capture_re.search(demangled_name)
        if args_capture:  # Fails if demangled name doesn't contain types
            # No need to pop `this` as its never in the demangled name
            # Also, don't append the type if it's `void` (void* though is accepted)
            return [
                normalize_type(v)
                for v in args_re.findall(args_capture.group(0))
                if v != 'void'
            ]

    if param_types and param_types != 'void':  # Skip empty strings, as they produce ['']
        return maybe_pop_this_from_array([normalize_type(t) for t in param_types.split('~') if t], cc)

    return []


def extract_param_names(param_names: str, cc: str):
    if param_names:
        return maybe_pop_this_from_array(param_names.split('~'), cc)

    return []


#  Returns a tuple of (Non-Virtual, and Virtual[Sorted by vmt index]) functions belonging to this class
def extract(class_name: str, database: Path, arg_types_from_demangled: bool):
    csv_path = database / 'plugin-sdk.out.functions.csv'
    if not csv_path.exists():
        raise FileNotFoundError('plugin-sdk.out.functions.csv not present. Try re-running IDA plugin-sdk exporter.')

    # Cols used and their respective type
    cols = {
        '10us': str,
        # 'Module': str,
        'Name': str,
        'DemangledName': str,
        'Type': str,
        'CC': str,
        'RetType': str,
        'ParamTypes': str,
        'ParamNames': str,
        # 'IsConst': bool,
        # 'Refs': np.int16,
        # 'Comment': str,
        # 'Priority': bool,
        'VTIndex': np.int16,
        # 'ForceOverloaded': bool
    }

    csv_df = read_csv(csv_path, dtype=cols, usecols=cols.keys(), engine='c', sep=',', na_values=[], keep_default_na=False)
    csv_df = csv_df[csv_df['DemangledName'].str.startswith(class_name)]  # Only class members
    csv_df.sort_values(inplace=True, by='VTIndex')
    csv_df.reset_index(inplace=True)

    # Create data that fits our needs, normalize types, etc..
    fn_series = csv_df[['ParamTypes', 'ParamNames', 'CC', 'DemangledName', 'RetType', 'VTIndex', '10us']].apply(
        lambda s: Function(
            cls=class_name,
            full_name=s[3],
            name=extract_function_from_demangled_name(s[3]),
            address=s[6],
            ret_type=normalize_type(s[4]),
            vt_index=s[5],
            cc=s[2],
            args=[
                (t, n)
                for t, n in zip(extract_param_types(s[0], s[2], s[3], arg_types_from_demangled), extract_param_names(s[1], s[2]))
            ]
        ),
        axis=1  # Apply on each row
    )

    filter_by_type = lambda ts: fn_series.loc[fn_series.apply(lambda f: f.type in ts)].tolist()
    dtor = filter_by_type([FunctionType.DTOR, FunctionType.DTOR_VIRTUAL])
    return {
        'ctors': filter_by_type([FunctionType.CTOR]),
        'dtor': dtor[0] if dtor else None,  # There can be only one destructor, so this has to be a single item, not a list
        'virtual_fns': filter_by_type([FunctionType.VIRTUAL]),
        'regular_fns': filter_by_type([FunctionType.REGULAR]),
    }
