import extractors.pluginsdk.Extractor
import extractors.fakepdb.Extractor
from args import DATABASE_TYPE

def extract(class_name : str):
    if DATABASE_TYPE == 'pluginsdk':
        return pluginsdk.Extractor.extract(class_name)
        
    elif DATABASE_TYPE == 'fakepdb':
        return fakepdb.Extractor.extract(class_name)
