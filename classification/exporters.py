from common.exporter import Exporter, Task
from django import forms


class ClassificationExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)


class ClassificationExporter(Exporter):
    task_type = Task.CLASSIFICATION
    name = 'Default image classification exporter'

    def export(self):
        print('Trying to export...')

    def get_form(self, data=None):
        return ClassificationExporterForm(data=data)

