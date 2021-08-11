import json
from pathlib import Path
from Variable import Variable

def Extract(className, db : Path):
    file = db / "structs" / f"gtaout.{className}.json"
    if not file.exists():
        return {}
    with file.open(mode='r', encoding='UTF-8') as f:
        j = json.loads(f.read())
        return {
            'member_vars': [Variable(address=m["offset"], full_name=m["name"], type=m["type"]) for m in j["members"]],
            'class_size': j["size"]
        }
