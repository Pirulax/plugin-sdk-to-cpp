import re
from typing import List

# Wraps all elements, then joins them
def wrap_join(sep : str, wrap_with : str, l : List[str]) -> str:
    return sep.join(wrap_with.format(v) for v in l)

# Make a match group that matches with any element of `list`
def re_make_match_group_for(match : List[str], capturing : bool) -> str:
    group = wrap_join("|", "(?:{0})", match) 
    return group if capturing else f'(?:{group})'

# Map of what to replace in format of <to>: {..what..}
# Case-insensitive, regex can be used, but it will be wrapped between \b
REPLACE_MAP = {
    # NOTE: Has to be on top! So regexes below don't have to include `signed` stuff
    # Basically remove everything in here.
    '': ('signed', 'struct', 'class'),

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

REPLACEMENT = [
    (
        re.compile(f'\\b{re_make_match_group_for(what, False)}\\b', flags=re.IGNORECASE), # Wrap match group regex between \b and compile
        to
    )
    for to, what in REPLACE_MAP.items()
]

def normalize_type(text: str):
    text = text.strip()

    for regex, repl in REPLACEMENT:
        (text, n_subs) = regex.subn(repl, text)
        if repl and n_subs:
            # Stop here, as the type has been successfully normalized 
            # repl == '' not included as it just removes useless noise
            break

    # Simply replace `char`. Can't be done with regex, because of `const char*`
    # NOTE: Regex has to be done first, to remove `signed` prefix
    if text == 'char':
        return 'int8_t'

    return text
