import re

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
    (r'\s+(?=\*)', '')  # Fix space between type and * for pointers (Eg.: Foo * => Foo*)
]
type_replacements = [(re.compile(regex), repl) for regex, repl in type_replacements]  # Compile all regexes


def normalize_type(text: str):
    if text == 'char':
        return 'int8_t'

    for regex, repl in type_replacements:
        text = regex.sub(repl, text)

    return text
