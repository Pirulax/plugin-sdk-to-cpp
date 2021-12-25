from models.Function import FunctionType
from pandas.core.frame import DataFrame
from pandas.core.series import Series

# https://stackoverflow.com/questions/363944
def first_of_list_or(list, default_value):
    return next(iter(list), default_value)

# Takes a Series of Function objects and categorizes it depending on function type
def categorize_fn_series_by_type(df : Series):
    # Get all functions by type as a py list
    get_all_by_type = lambda ts: df[df.apply(lambda f: f.type in ts)].tolist()

    return {
        # There can be only one destructor, so this has to be a single item, not a list
        'dtor': first_of_list_or(get_all_by_type((FunctionType.DTOR, FunctionType.DTOR_VIRTUAL)), None), 
        'ctors': get_all_by_type((FunctionType.CTOR, )),
        'virtual_methods': get_all_by_type((FunctionType.VIRTUAL, )),
        'methods': get_all_by_type((FunctionType.METHOD, )), 
        'static_fns': get_all_by_type((FunctionType.STATIC, ))
    }