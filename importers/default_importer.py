from common.importer import Importer
from django import forms
from annotationweb.models import ImageSequence
import os
import fnmatch


class DefaultImporterForm(forms.Form):
    path = forms.CharField(label='Data path', max_length=1000)

    # TODO validate path

    def __init__(self, data=None):
        super().__init__(data)


class DefaultImporter(Importer):

    name = 'Default importer'
    dataset = None

    def get_form(self, data=None):
        return DefaultImporterForm(data)

    def import_data(self, form):
        if self.dataset is None:
            raise Exception('Dataset must be given to importer')

        # Crawl recursively in path to find all images and add them to db
        for root, dirnames, filenames in os.walk(form.cleaned_data['path']):
            for filename in fnmatch.filter(filenames, '*.png'):
                image = ImageSequence()
                image.format = os.path.join(root, filename)
                image.nr_of_frames = 1
                image.dataset = self.dataset
                image.save()
                print('Saved image ', image.filename)
        return True, form.cleaned_data['path']
