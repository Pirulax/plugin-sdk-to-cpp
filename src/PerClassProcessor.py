from args import OUTPUT_PATH
import jinja2 as j2
import CSVFunctionExtract
import CSVStaticVariableExtract
import JSONStructExtract

def process(class_name : str):
    j2env = j2.Environment(
        loader=j2.FileSystemLoader(searchpath='templates/'),
        autoescape=None,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )
 
    j2env.globals.update({
        'class_name': class_name,
        'static_vars': CSVStaticVariableExtract.extract(class_name),
        **CSVFunctionExtract.extract(class_name),
        **JSONStructExtract.extract(class_name)
    })

    for template, out_ext in (('source', 'cpp'), ('header', 'h')):
        with (OUTPUT_PATH / f'{class_name}.{out_ext}').open('w', encoding='UTF-8') as file:
            file.write(j2env.get_template(f'{template}.jinja2').render())
