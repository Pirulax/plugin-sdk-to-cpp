import re
from dataclasses import dataclass
import warnings

# Matches array subscript only. Eg: [][32]
subscript_re = re.compile(r'((?:(?:\s*\[[\d\s]*\]))+)')

def remove_all_extents(t : str):
    # Does the same as std::remove_all_extents
    # Return T, and subscript of array.
    # Eg.: type = "char[10]", this function will return "char", "[10]"

    subscript_match = subscript_re.search(t)
    if subscript_match:
        subscript = subscript_match.group(1)
        return t.replace(subscript, '').strip(), subscript.strip()

    return t.strip(), None

@dataclass
class Variable:
    address: str                   # Address/Offset in hex format. Like 0xBADBEEF
    type: str                      # Full extent type, like int[10], int, int*, etc..
    full_name: str                 # Name with class, eg.: CTimer::m_sTime
    namespaceless_name: str = None # Name without class/namesapce. Eg.: m_sTime
    no_extent_type: str = None     # Type, like `unsigned int`. This is basically the same type as std::remove_all_extents would return
    array_subscript: str = None    # Array subscript, like: [10], [32][32], [][32], etc...
    is_type_pointer : bool = False # Is the our type a pointer? That is, if `type` contains a `*`

    def __post_init__(self):
        # TODO (Izzotop): Fix that
        if self.type:
            self.no_extent_type, self.array_subscript = remove_all_extents(self.type)
        else:
            warnings.warn(f"Type of {self.full_name} not defined. Using `None` instead. To fix this, go to IDA, press Y on this variable, then enter, reexport, and you are gtg")

        if not self.namespaceless_name:
            self.namespaceless_name = self.full_name

        self.is_type_pointer = self.type.find('*') != -1
