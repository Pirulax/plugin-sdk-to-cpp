#
# Inteface for FakePDB .json dump
#
# NOTE:
# Doesn't support virtual functions yet. (As vtable indices aren't dumped)
#

from pathlib import Path
from src.models.Function import Function, FunctionType
from Util import does_belong_to_class
import pandas
from src.args import DATABASE_PATH
from pandas import Series, DataFrame
from models import Variable
from type_replacement import normalize_type
from extractors.Extractor import categorize_fn_series_by_type

def all_matching(iterable, condition):
    for var in iterable:
        if condition(var):
            yield var

# Based on https://stackoverflow.com/a/35513376/15363969
def first(iterable, condition):
    return next(all_matching(iterable, condition))

def process_class_struct(class_name : str, json_dump):

    # Find sturct by name
    class_struct = first(json_dump['structs'], lambda st: st['type'] == class_name)
    if not class_struct:
        raise RuntimeError(f"Failed to locate structure for class {class_name}")

    # Process member variables, and return data
    return {
        'class_size': hex(class_struct["size"]),
        'member_vars': [
            Variable(
                address=member['offset'],
                full_name=member['name'],
                type=normalize_type(member['type'])
            )
            for member in class_struct['members']
        ]
    }

def process_class_static_vars(class_name : str, json_dump):
    return [
        Variable(
            address=var['offset'],
            full_name=var['name_demangled'],
            type=normalize_type(var['type'])
        )
        for var in json_dump['names']
        if does_belong_to_class(class_name, var['name_demangled'])
    ]

# class_name : str, 
# address : str, 
# demangled_name : str, 
# cc : str, 
# ret_type : str, 
# arg_types : str, 
# arg_names : str, 
# vt_index : np.int16, 
# is_overloaded : bool
def process_class_functions(class_name : str, json_dump):

    # Make a dataframe out of the data
    fns_df = DataFrame([
        fn
        for fn in json_dump['functions']
        if does_belong_to_class(class_name, fn['name_demangled'])  
    ])

    # Rename some columns, so we can directly unpack the series to construct the Function object
    fns_df.rename({
        'start_rva': 'address',
        'name_demangled': 'demangled_name',
        'calling_convention': 'cc',
        'return_type': 'ret_type'
    })

    # Originally addresses are relative to the PE image base
    # but we need absolute addresses.
    # In case of GTA the base is 0x400000
    fns_df['address'].apply(lambda a: 0x400000 + a,inplace=True) # Add exe base to RVA to get the real address. TODO: use pe base here

    # Add `is_overloaded` for each function
    fns_df['is_overloaded'] = fns_df['name_demangled'].duplicated(keep=False)

    # Extract arg types
    fns_df['arg_types'] = fns_df['arguments'].apply(lambda args: [a['type'] for a in args])

    # Extract arg names
    fns_df['arg_names'] = fns_df['arguments'].apply(lambda args: [a['name'] for a in args])

    return categorize_fn_series_by_type(fns_df.apply(
        lambda fn: Function(class_name=class_name, vt_index=-1, **fn),
        axis=1
    ))
        
def extract(class_name : str):
    if not DATABASE_PATH.exists():
        raise FileNotFoundError("FakePDB .json dump not found at the specified path!")

    df = pandas.read_json(DATABASE_PATH, typ='series')
    return {
        **process_class_struct(class_name, df),
        **process_class_functions(class_name, df),
        'static_vars': process_class_static_vars(class_name, df),
    }
