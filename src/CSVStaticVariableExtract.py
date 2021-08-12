from pathlib import Path
from pandas import read_csv
import numpy as np
import re
from Variable import Variable


strip_name_re = re.compile(r'::(\w+)')
def StripName(demangledName):
    return strip_name_re.search(demangledName).group(1)

# Returns a DataFrame of variables belonging to this class
def Extract(className : str, database : Path):
    csv_path = database / "plugin-sdk.out.variables.csv"
    if not csv_path.exists():
        raise FileNotFoundError("plugin-sdk.out.variables.csv not present. Try re-running IDA plugin-sdk exporter.")
    cols = {
        "10us": str,
        #'Module': str,
        #'Name': str,
        'DemangledName': str,
        'Type': str,
        #'RawType': str,
        'Size': np.int32,
        #'Comment': str,
        'IsReadOnly': bool
    }
    csv_df = read_csv(csv_path, engine='c', sep=',', usecols=cols.keys(), dtype=cols, na_values=[], keep_default_na=False)
    csv_df = csv_df.loc[lambda s: s['DemangledName'].str.startswith(className)] 
    return csv_df[['10us', 'Type', 'DemangledName']].apply(lambda s: Variable(
        address = s[0],
        stripped_name=StripName(s[2]),
        full_name=s[2],
        type=s[1]
    ), axis=1,result_type='reduce').to_list()


    """ df = csv_df[['10us', 'Type', 'DemangledName']].apply(lambda s: (s[0], StripName(s[2])) + RemoveAllExtents(s[1]))
    df.columns = ['Address', 'StrippedName', 'TypeNoExtents', 'ArraySubScript']
    return df """
