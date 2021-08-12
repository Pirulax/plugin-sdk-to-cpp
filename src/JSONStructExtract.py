import json
from pathlib import Path

from models.Variable import Variable
from type_replacement import normalize_type


def extract(class_name, db: Path):
    file_path = db / 'structs' / f'gtaout.{class_name}.json'
    if not file_path.exists():
        # Static class
        return {'class_size': '0x0'}

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
