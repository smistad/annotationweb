from os.path import basename

import importlib
import glob
import os
from annotationweb.settings import BASE_DIR

exporters = []


class MetaExporter(type):

    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))
        if name != 'Exporter':
            print('Found the exporter class', name)
            exporters.append(result)
        return result


class Exporter(metaclass=MetaExporter):

    def get_form(self, data=None):
        raise NotImplementedError('An exporter needs to implement an export method')

    def export(self, form):
        raise NotImplementedError('An exporter needs to implement an export method')


def find_all_exporters(task_type):
    result = []

    modules = glob.glob(os.path.join(BASE_DIR, task_type, 'exporters') + '/*.py')
    for module in modules:
        print('Importing..')
        exporters.clear()
        module_name = basename(module)[:-3]
        foo = importlib.machinery.SourceFileLoader(module_name, module).load_module()
        for exporter in exporters:
            result.append(exporter)

    return result
