import re
from dataclasses import dataclass
from typing import Optional
import warnings
from models import Type

@dataclass
class Variable:
    address: int            # Address/Offset in hex format. Like 0xBADBEEF
    full_name: str          # Name with class, eg.: `CTimer::m_sTime``
    namespaceless_name: str # Name without class/namesapce. Eg.: `m_sTime`
    type: Type              # Full extent type, like int[10], int, int*, etc..

    def __init__(self, address : int, full_name : str, type : Type, namespaceless_name : Optional[str] = None):
        if type:
            self.type = Type(type)
        else:
            self.type = None
            warnings.warn(f"Type of {self.full_name} not defined. Using `None` instead. To fix this, go to IDA, press Y on this variable, then enter, reexport, and you are gtg")

        self.address = address
        self.full_name = full_name
        self.namespaceless_name = namespaceless_name or self.full_name

    @property
    def address_hex(self):
        return f'0x{self.address:X}'
