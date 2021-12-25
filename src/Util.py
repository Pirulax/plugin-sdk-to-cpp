import re

# Checks if name starts with {class_name}(?:__|::)
# Eg.:
# does_belong_to_class("CPed", "CPed::Load()") => True
# does_belong_to_class("CPed", "CPed__Save()") => True
# does_belong_to_class("CPed", "CPedAttractor::Init") => False
def does_belong_to_class(class_name, what) -> bool:
    return bool(re.match(f'{class_name}(?:__|::)', what))
