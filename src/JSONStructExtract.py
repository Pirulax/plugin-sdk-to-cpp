import json
from pathlib import Path
from models.Variable import Variable
from type_replacement import normalize_type
from args import DATABASE_PATH


def extract(cls_name : str) -> tuple[list[Variable], int]:
    """
    Extract the struct from the JSON file

    :param cls_name: The class name
    
    :return: A tuple with the list of variables and the size of the struct. Size is 0 if the struct is static (that is, it's JSON file can't be found)
    """

    file_path = DATABASE_PATH / 'structs' / f'gtaout.{cls_name}.json'
    if not file_path.exists():
        return ([], 0) # Static class

    with file_path.open(mode='r', encoding='UTF-8') as file:
        data = json.load(file)
        return (
            [
            Variable(
                address=member['offset'],
                full_name=member['name'],
                type=normalize_type(member['type'])
            )
            for member in data['members']
            ], 
            int(data['size'], base=16)
        )
