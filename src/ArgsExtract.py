from models.CallingConvention import CallingConvention
from args import ARG_TYPES_FROM_DEMANGLED_NAME
import re
from type_replacement import normalize_type
from typing import List, Tuple

# Pops first extracted value from `what` if the calling convetion corresponds to a method's
# `what` should be a string with values separated by `~`
def split_maybe_pop_first(what : str, cc : CallingConvention):
    if not what: # Empty string produces [''], so lets not do that
        return []

    split = what.split('~')
    if cc.is_method:
        return split[1:] # Slice off `this`

    return split

args_capture_re = re.compile(r'\((.+?)\)')
args_re = re.compile(r'(\w+\s*\*?\s*?(?<![,\)]))')

def names(names_str : str, cc : CallingConvention) -> List[str]:
    return split_maybe_pop_first(names_str, cc)

# Extract parameter types from demangled name or `types_str`
# depending on the program arguments
# `types_str` - should be a list of types in a string separated by `~`
# `names_str` - should be a list of names in a string separated by `~`
def types(types_str : str, arg_names : List[str], dem_name : str, cc : CallingConvention) -> List[str]:
    if ARG_TYPES_FROM_DEMANGLED_NAME:
        args_capture = args_capture_re.search(dem_name) # Match argument list
        if args_capture: # Fails if demangled name doesn't contain types
            args_capture_str = args_capture.group(1)

            if args_capture_str.strip() in ('void', ''): # no parameters
                return []
                
            # Clever trick: 
            # Instead of trying to match complex C++ types, we just
            # sub all the arg names, this way only the types remain
            # then we split by `, `, and heureka, we've got a list of types
            arg_types = re.sub('\s*({})\s*'.format('|'.join(arg_names)), '', args_capture_str).split(',')

            # No need to go though `split_maybe_pop_first`, because `this` is never in the demangled name
            return [normalize_type(v.strip()) for v in arg_types]

    if types_str != 'void':
        return [normalize_type(t) for t in split_maybe_pop_first(types_str, cc)]

    return []

def extract(types_str : str, names_str : str, dem_name : str, cc : CallingConvention):
    arg_names = names(names_str, cc)
    return arg_names, types(types_str, arg_names, dem_name, cc)
