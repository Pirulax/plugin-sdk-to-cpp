#
# Inteface for PluginSDK exported database
#

from extractors.pluginsdk import FunctionExtract, StaticVariableExtract, StructExtract

def extract(class_name : str):
    return {
        'static_vars': StaticVariableExtract.extract(class_name)
        **FunctionExtract.extract(class_name),
        **StructExtract.extract(class_name),
    }
