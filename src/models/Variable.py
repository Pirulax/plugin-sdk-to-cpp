import re
from dataclasses import dataclass
from typing import Optional
import warnings
from models import Type

@dataclass
class Variable:
    address: int            # Address/Offset
    full_name: str          # Name with class, eg.: `CTimer::m_sTime``
    namespaceless_name: str # Name without class/namesapce. Eg.: `m_sTime`
    type: Type              # Full extent type, like int[10], int, int*, etc..

    def __init__(self, address : int, full_name : str, type : Type, namespaceless_name : Optional[str] = None):
        if type:
            self.type = Type(type)
        else:
            self.type = Type('void')
            warnings.warn(f"Type of {full_name} not defined. Using `void` instead. To fix this, go to IDA, press Y on this variable, then enter, reexport, and you are gtg")

        self.address = address
        self.full_name = full_name
        self.namespaceless_name = namespaceless_name or self.full_name

    @property
    def address_hex(self):
        """Address but in hex format"""
        return f'0x{self.address:X}'
    
    @property
    def definition_code(self):
        """Get C++ definition code of this type"""
        return f'auto& {self.namespaceless_name} = StaticRef<{self.type.definition_type}, {self.address_hex}>()'
