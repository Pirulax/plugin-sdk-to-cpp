from dataclasses import dataclass
import re

extract_info_from_type_re = re.compile(r'(\w+)((?:\[\d*\])+)?')
def RemoveAllExtents(type):
    # Does the same as std::remove_all_extents
    # Return T, and subscript of array.
    # Eg.: type = "char[10]", this function will return "char", "[10]"
    match = extract_info_from_type_re.search(type)
    return match.group(1), match.group(2)

@dataclass
class Variable:
    address : str                   # Adderss in hex format. Like 0xBADBEEF
    type : str                      # Full extent type, like int[10], int, int*, etc..
    full_name : str                 # Name with class, eg.: CTimer::m_sTime    
    stripped_name : str = None      # Name without class. Eg.: m_sTime
    no_extent_type : str = None     # Type, like `unsigned int`. This is basically the same type as std::remove_all_extents would return
    array_subscript : str = None    # Array subscript, like: [10], [32][32], [][32], etc...
    
    def __post_init__(self):
        self.no_extent_type, self.array_subscript = RemoveAllExtents(self.type)
        if not self.stripped_name:
            self.stripped_name = self.full_name