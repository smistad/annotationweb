from os.path import basename
import importlib
import glob
from distutils import dirname

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

    modules = glob.glob(dirname(__file__) + "/*.py")
    for module in modules:
        module = basename(module)[:-3]
        print('Found importers module: ', module)
        spec = importlib.util.find_spec('importers.' + module)
        if spec is not None:
            print('Importing..')
            importers.clear()
            foo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(foo)
            for importer in importers:
                result.append(importer)
        else:
            print('Spec was none in ', module)

    return result
