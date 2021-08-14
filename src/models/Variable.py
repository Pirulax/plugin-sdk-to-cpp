import re
from dataclasses import dataclass

# Matches array subscript only. Eg: [][32]
subscript_re = re.compile(r'((?:(?:\s*\[[\d\s]*\]))+)')

def remove_all_extents(t):
    # Does the same as std::remove_all_extents
    # Return T, and subscript of array.
    # Eg.: type = "char[10]", this function will return "char", "[10]"

    subscript_match = subscript_re.search(t)
    if subscript_match:
        subscript = subscript_match.group(1)
        return t.replace(subscript, ''), subscript

    return t, None


@dataclass
class Variable:
    address: str                 # Address/Offset in hex format. Like 0xBADBEEF
    type: str                    # Full extent type, like int[10], int, int*, etc..
    full_name: str               # Name with class, eg.: CTimer::m_sTime
    stripped_name: str = None    # Name without class. Eg.: m_sTime
    no_extent_type: str = None   # Type, like `unsigned int`. This is basically the same type as std::remove_all_extents would return
    array_subscript: str = None  # Array subscript, like: [10], [32][32], [][32], etc...

    def __post_init__(self):
        # TODO (Izzotop): Fix that
        if self.type != '':
            self.no_extent_type, self.array_subscript = remove_all_extents(self.type)

        if not self.stripped_name:
            self.stripped_name = self.full_name
