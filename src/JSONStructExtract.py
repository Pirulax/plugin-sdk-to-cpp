import json
from pathlib import Path

from models.Variable import Variable


def extract(class_name, db: Path):
    file_path = db / 'structs' / f'gtaout.{class_name}.json'
    if not file_path.exists():
        # Static class
        return {'class_size': '0x0'}

    with file_path.open(mode='r', encoding='UTF-8') as file:
        j = json.loads(file.read())
        return {
            'member_vars': [Variable(address=m['offset'], full_name=m['name'], type=m['type']) for m in j['members']],
            'class_size': j['size']
        }
