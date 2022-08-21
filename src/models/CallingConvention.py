from enum import Enum

class CallingConvention(Enum):
    def __new__(cls, value, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, strname, is_method, plugin_fn, is_special):
        self.is_method = is_method      # Is this convention used for methods
        self.plugin_fn = plugin_fn      # Respective plugin:: function with which this cc is called with
        self.is_special = is_special    # See `has_to_speficy`

    THIS_CALL = ('thiscall', True,  'CallMethod', False)
    FAST_CALL = ('fastcall', True,  'FastCall',   True)
    CDECL     = ('cdecl',    False, 'Call',       False)
    STDCALL   = ('stdcall',  False, 'Call',       True)

    @property
    def is_static(self):
        return not self.is_method
    
    @property
    def has_to_specify(self):
        # True if the CC has to be specified in the function def/decl, False otherwise
        return self.is_special
