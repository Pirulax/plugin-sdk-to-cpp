import re
from pathlib import Path

import numpy as np
from pandas import read_csv

from models.Function import FunctionType, Function
from type_replacement import normalize_type

# Extract function name from DemangledName column
name_re = re.compile(r'::(~?\w+)\(*?')


def extract_name_from_demangled(demangled_name : str):
    name = demangled_name.replace('__', '::')
    return name_re.search(name).group(1)


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

    csv_df['StrippedName'] = csv_df['DemangledName'].apply(lambda dn: extract_name_from_demangled(dn))
    csv_df['IsOverloaded'] = csv_df['StrippedName'].duplicated(keep=False)

    #all_functions = set()
    #fn_series.apply(lambda fn: all_functions.add(fn))

    # Create data that fits our needs, normalize types, etc..
    fn_series = csv_df[['ParamTypes', 'ParamNames', 'CC', 'DemangledName', 'RetType', 'VTIndex', '10us', 'StrippedName', 'IsOverloaded']].apply(
        lambda s: Function(
            cls=class_name,
            full_name=s[3],
            name=s[7],
            address=s[6],
            ret_type=normalize_type(s[4]),
            vt_index=s[5],
            cc=s[2],
            is_overloaded=s[8],
            args=[
                (t, n)
                for t, n in zip(extract_param_types(s[0], s[2], s[3], arg_types_from_demangled), extract_param_names(s[1], s[2]))
            ]
        ),
        axis=1  # Apply on each row
    )
    # Find all duplicates and mark them as such
    #all_functions = set()
    #fn_series.apply(lambda fn: all_functions.add(fn))
    #fn_series[fn_series.apply(lambda fn: fn in all_functions)].apply(lambda fn: fn.is_overloaded)


    filter_by_type = lambda ts: fn_series.loc[fn_series.apply(lambda f: f.type in ts)].tolist()
    dtor = filter_by_type([FunctionType.DTOR, FunctionType.DTOR_VIRTUAL])
    return {
        'ctors': filter_by_type([FunctionType.CTOR]),
        'dtor': dtor[0] if dtor else None,  # There can be only one destructor, so this has to be a single item, not a list
        'virtual_fns': filter_by_type([FunctionType.VIRTUAL]),
        'regular_fns': filter_by_type([FunctionType.REGULAR]),
    }
