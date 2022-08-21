from models.CallingConvention import CallingConvention
from args import ARG_TYPES_FROM_DEMANGLED_NAME
import re
from models import Type

def extract_names_pop_this(args : str, cc : CallingConvention):
    """
    :param args: List of argument names separated by `~`
    :param cc: Calling convention of the function
    :return: List of argument names without `this` (if `cc.is_method`)
    """

    if not args: # Empty string produces [''], so lets not do that
        return []

    split = args.split('~')    
    return split[1:] if cc.is_method else split # splice => removes `this`


# Regex to match the `( ... )` part of a function signature (that is, where the arguments are)
# group 1 contains the arguments
FN_ARGS_CAPTURE_REGEX = re.compile(r'\((.+?)\)')

def extract_types(types_str : str, arg_names : list[str], fn_dem_name : str, cc : CallingConvention) -> list[str]:
    """
    Extract parameter types from demangled name or 
    `types_str` depending on the program arguments.

    :param types_str: - should be a list of types in a string separated by `~`
    :param names_str: - should be a list of names in a string separated by `~`

    :returns: Parameter types (without `this`'s type if `cc.is_method`)
    """

    if ARG_TYPES_FROM_DEMANGLED_NAME:
        fn_args = FN_ARGS_CAPTURE_REGEX.search(fn_dem_name) # Match argument list
        if fn_args: # Fails if demangled name doesn't contain types
            args_capture_str = fn_args.group(1)

            if args_capture_str.strip() in ('void', ''): # no parameters
                return []
                
            # Clever trick: 
            # Instead of trying to match complex C++ types, we just
            # sub all the arg names, this way only the types remain
            # then we split by `, `, and heureka, we've got a list of types
            arg_types = re.sub('\s*({})\s*'.format('|'.join(arg_names)), '', args_capture_str).split(',')

            # No need to go though `split_maybe_pop_first`, because `this` is never in the demangled name
            return [Type(v) for v in arg_types]

    if types_str in ('void', ''):
        return []

    return [Type(t) for t in extract_names_pop_this(types_str, cc)]

def extract(types_str : str, names_str : str, fn_dem_name : str, cc : CallingConvention):
    """
    :param types_str: The argument types separated by `~`
    :param names_str: The argument names separated by `~`
    :param fn_dem_name: The demangled name of the function (Used to extract argument types if `ARG_TYPES_FROM_DEMANGLED_NAME` is True)
    :param cc: Calling convention of the function (Used to know if `this` has to be popped of the argument list)
    """

    arg_names = extract_names_pop_this(names_str, cc)
    return arg_names, extract_types(types_str, arg_names, fn_dem_name, cc)
