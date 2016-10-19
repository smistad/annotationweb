from importers.importer import Importer
from django import forms
from annotationweb.models import Image
import os
import fnmatch


class DefaultImporterForm(forms.Form):
    path = forms.CharField(label='Data path', max_length=1000)

    # TODO validate path

    def __init__(self, data=None):
        super().__init__(data)


class DefaultImporter(Importer):

    name = 'Default importer'

    def get_form(self, data=None):
        return DefaultImporterForm(data)

    def import_data(self, form):
        # Crawl recursively in path to find all images and add them to db
        for root, dirnames, filenames in os.walk(form.cleaned_data['path']):
            for filename in fnmatch.filter(filenames, '*.png'):
                image = Image()
                image.filename = os.path.join(root, filename)
                image.dataset = self.dataset
                image.save()
                print('Saved image ', image.filename)
        return True, form.cleaned_data['path']
