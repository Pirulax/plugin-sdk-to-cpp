from functools import cache
from typing import Optional
import re

def re_make_match_group_for(to_match : list[str]) -> str:
    """
    Make a capturing match group that matches with any element of `to_match`
    """
    
    return f"(?:{'|'.join(f'(?:{v})' for v in to_match)})"

# Map of what to replace in format of <to>: {..what..}
# Case-insensitive, regex can be used, but it will be wrapped between \b
REPLACE_MAP = {
    # From here on if there's a match the loop will break,
    # and wont perform anymore replacements
    # This is done, because, logically, once the type has been normalized
    # it won't match any other group's criteria
    'uint8': ('uchar', 'unsigned char', 'unsigned __int8', '_byte', 'byte', 'uint8', 'uint8_t', ),
    'int8': ('__int8', 'int8', 'int8_t', ), # dont wanna replace `char` because of `const char*`

    'uint16': ('ushort', 'unsigned short',  'unsigned __int16', 'uint16', 'uint16_t', ),
    'int16': ('short', '__int16', 'word', '_word', 'int16', 'int16_t', ),

    'uint32': ('uint', 'unsigned int', 'unsigned __int32', 'uint32', 'uint32_t', ),
    'int32': ('int', '__int32','dword', '_dword', 'int32', 'int32_t', ),

    'bool': ('_BOOL1', )
}

# These things are completely removed from the type name
REMOVE_FROM_TYPE = ('signed', 'struct', 'class')
REMOVE_FROM_TYPE_REGEX = re.compile(f"{re_make_match_group_for(REMOVE_FROM_TYPE)}", flags=re.IGNORECASE)

REPLACEMENT = [
    (
        re.compile(f'\\b{re_make_match_group_for(replace_what_regex)}\\b', flags=re.IGNORECASE), # Wrap match group regex between \b and compile
        replace_with
    )
    for replace_with, replace_what_regex in REPLACE_MAP.items()
]

def normalize_type(type_str: str) -> str:
    """
    Normalize type name into something we use in our code.
    See `REPLACE_MAP` above.
    """

    type_str = type_str.strip()
    type_str = REMOVE_FROM_TYPE_REGEX.sub('', type_str)

    for replace_what_regex, replace_with in REPLACEMENT:
        (type_str, n_subs) = replace_what_regex.subn(replace_with, type_str)
        if n_subs:
            # Stop here, as the type has been successfully normalized
            # As logically, once the type has been normalized it won't match any other group's regex
            break

    # Simply replace `char`. Can't be done with regex, because of `const char*`
    # NOTE: Regex has to be done first, to remove `signed` prefix
    if type_str == 'char':
        return 'int8'

    return type_str


SUBSCRIPT_REGEX = re.compile(r'((?:(?:\s*\[[\d\s]*\]))+)')
def remove_all_extents(t : str):
    """
    Does the same as std::remove_all_extents_t<T>
    Eg.: 
        - char[10] => "char", [10]
        - float*  => float*
        - float => float

    :return: T, and subscript of array.
    """

    if subscript_match := SUBSCRIPT_REGEX.search(t):
        subscript = subscript_match.group(1)
        return t.replace(subscript, '').strip(), subscript.strip()

    return t.strip(), None

BUILTIN_TYPES    = {'bool', 'char', 'int', 'float', 'double', 'long', 'long long', 'short', 'unsigned char', 'unsigned int', 'unsigned long', 'unsigned long long', 'unsigned short', 'void'}

# A regex to decay a C++ type emove all extents, references, const, volatile, etc.
# NOTE: This regex is not 100% accurate, but it's good enough for our purposes
DECAY_TYPE_REGEX = re.compile(r'''
    (?:
        (?:(?:\s*\[[\d\s]*\])+) # subscripts
        |(?:(?:\s*\*+)+) # pointers
        |(?:(?:\s*const)+) # const
        |(?:(?:\s*volatile)+) # volatile
        |(?:(?:\s*&+)+) # references
    )
''', flags=re.VERBOSE)

class Type:
    """
    Represents a C++ type
    """

    __slots__ = ('full_type', 'no_extent_type', 'array_subscript', 'is_pointer',)

    full_type : str                 # The full type name, eg.: `int[10]`, `int`, `int*`, etc...
    no_extent_type : str            # See `remove_all_extents`
    array_subscript : Optional[str] # If type is an array, this is the subscript. Eg: [10], [32][32], [][32], etc...
    is_pointer : bool               # Whenever the type is a pointer

    def __init__(self, full_type : str, normalize : bool = True):
        self.full_type = normalize_type(full_type) if normalize else full_type
        self.no_extent_type, self.array_subscript = remove_all_extents(self.full_type)
        self.is_pointer = full_type.find('*') != -1

    @property
    @cache
    def is_builtin(self):
        return not self.full_type.startswith("C") or self.full_type in BUILTIN_TYPES

    @property
    def decay_type(self):
        # Same as `std::decay_t<T>`
        # Eg.:
        # - int* => int
        # - int[10] => int
        # - int& => int
        # - ...

        return DECAY_TYPE_REGEX.sub('', self.full_type).strip()

    def __str__(self):
        return self.full_type

    def __hash__(self):
        return hash(self.full_type)
