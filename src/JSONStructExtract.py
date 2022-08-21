import json
from pathlib import Path
from typing import Optional, TypedDict
from models.Variable import Variable
from args import DATABASE_PATH

class StructInfo(TypedDict):
    variables : list[Variable]
    size : Optional[int]          # None if size is `0x0``
    vtbl_size : Optional[int]     # None if vtableSize is not present
    vtbl_addr : Optional[int]     # None if vtableAddress is not present

def extract(cls_name : str) -> StructInfo:
    """
    Extract the struct from the JSON file

    :param cls_name: The class name
    
    :return: A tuple with the list of variables, size of the struct and vtable address. Size is 0 if the struct is static (that is, it's JSON file can't be found)
    """

    file_path = DATABASE_PATH / 'structs' / f'gtaout.{cls_name}.json'
    if not file_path.exists():
        return StructInfo(
            variables=[], 
            size=None,
            vtbl_size=None,
            vtbl_addr=None
        )

    def get_int_from_dict(dct : dict, key, base) -> Optional[int]:
        match dct.get(key, None):
            case None:
                return None
            case int() as value:
                return value
            case str() as value:
                return int(value, base=base)
    
    get_data_int = lambda key, base : get_int_from_dict(data, key, base)

    with file_path.open(mode='r', encoding='UTF-8') as file:
        data = json.load(file)
        return StructInfo(
            variables=[
                Variable(
                    address=get_int_from_dict(member, "offset", 16),
                    full_name=member['name'],
                    type=member['type']
                )
                for member in data['members']
            ],
            size=get_data_int('size', 16),
            vtbl_size=get_data_int('vtableSize', 10),
            vtbl_addr=get_data_int('vtableAddress', 16)
        )
