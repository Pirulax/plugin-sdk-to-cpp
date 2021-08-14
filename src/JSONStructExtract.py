import json
from pathlib import Path
from models.Variable import Variable
from type_replacement import normalize_type
from args import DATABASE_PATH

def extract(class_name : str):
    file_path = DATABASE_PATH / 'structs' / f'gtaout.{class_name}.json'
    if not file_path.exists():
        return {'class_size': '0x0'} # Static class

    with file_path.open(mode='r', encoding='UTF-8') as file:
        data = json.loads(file.read())
        members = [
            Variable(
                address=member['offset'],
                full_name=member['name'],
                type=normalize_type(member['type'])
            )
            for member in data['members']
        ]
        return {
            'member_vars': members,
            'class_size': data['size']
        }
