import re
from pathlib import Path

import numpy as np
from pandas import read_csv

from models.Function import FunctionType, Function
from type_replacement import normalize_type

from args import DATABASE_PATH

# Extract function name from DemangledName column
name_re = re.compile(r'::(~?\w+)\(*?')


def extract_name_from_demangled(demangled_name : str):
    name = demangled_name.replace('__', '::')
    return name_re.search(name).group(1)

# https://stackoverflow.com/questions/363944
def first_of_list_or(list, default_value):
    return next(iter(list), default_value)

#  Returns a tuple of (Non-Virtual, and Virtual[Sorted by vmt index]) functions belonging to this class
def extract(class_name: str):
    csv_path = DATABASE_PATH / 'plugin-sdk.out.functions.csv'
    if not csv_path.exists():
        raise FileNotFoundError('plugin-sdk.out.functions.csv not present. Try re-running IDA plugin-sdk exporter.')

    # Cols used and their respective (type, our name)
    cols = {
        '10us': (str, 'address'),
        'Name': (str, 'full_name'),
        'DemangledName': (str, 'demangled_name'),
        'CC': (str, 'cc'),
        'RetType': (str, 'ret_type'),
        'ParamTypes': (str, 'arg_types'),
        'ParamNames': (str, 'arg_names'),
        'VTIndex': (np.int16, 'vt_index'),
        #'Type': (str, 'prototype'),
        # 'Module': str,
        # 'IsConst': bool,
        # 'Refs': np.int16,
        # 'Comment': str,
        # 'Priority': bool,
        # 'ForceOverloaded': bool
    }

    csv_df = read_csv(csv_path, dtype={k: v[0] for k, v in cols.items()}, usecols=cols.keys(), engine='c', sep=',', na_values=[], keep_default_na=False)
    csv_df.rename(columns={k: v[1] for k, v in cols.items()}, inplace=True) # Rename columns in order for Function constructor to work
    csv_df = csv_df[csv_df['demangled_name'].str.startswith(class_name + '::')]  # Filter to only contain class members

    # Add these 2 columns
    csv_df['stripped_name'] = csv_df['demangled_name'].apply(lambda dn: extract_name_from_demangled(dn))
    csv_df['is_overloaded'] = csv_df['stripped_name'].duplicated(keep=False)
    
    # Sort virtual methods. Important, otherwise 
    # their VMT indices won't wont match up with GTAs
    csv_df.sort_values(inplace=True, by='vt_index')
    csv_df.reset_index(inplace=True)

    # Create Function objects
    fns = csv_df.apply(
        lambda s: Function(class    _name=class_name, **s),
        axis=1  # Apply on each row
    )
    
    # TODO Maybe do some checks here (Eg.: Check for duplicate destructors)

    # Get all functions by type as a py list
    get_all_by_type = lambda ts: fns[fns.apply(lambda f: f.type in ts)].tolist()

    return {
        # There can be only one destructor, so this has to be a single item, not a list
        'dtor': first_of_list_or(get_all_by_type((FunctionType.DTOR, FunctionType.DTOR_VIRTUAL)), None), 
        'ctors': get_all_by_type((FunctionType.CTOR, )),
        'virtual_methods': get_all_by_type((FunctionType.VIRTUAL, )),
        'methods': get_all_by_type((FunctionType.METHOD, )), 
        'static_fns': get_all_by_type((FunctionType.STATIC, ))
    }