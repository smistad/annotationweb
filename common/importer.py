from os.path import basename
import importlib
import glob
import os
from annotationweb.settings import PROJECT_PATH

importers = []


class MetaImporter(type):

    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))
        if name is not 'Importer':
            print('Found the importer class', name)
            importers.append(result)
        return result


class Importer(metaclass=MetaImporter):

    def get_form(self, data=None):
        raise NotImplementedError('An importer needs to implement a get_form method')

    def import_data(self, form):
        raise NotImplementedError('An importer needs to implement an import_data method')


def find_all_importers():
    result = []

    # Go through each app and see if there is an exporters.py file

    modules = glob.glob(os.path.join(PROJECT_PATH, 'importers') + "/*.py")
    for module in modules:
        print('Importing..')
        importers.clear()
        module_name = basename(module)[:-3]
        foo = importlib.machinery.SourceFileLoader(module_name, module).load_module()
        for importer in importers:
            result.append(importer)

    return result
