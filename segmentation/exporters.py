from common.exporter import Exporter
from common.metaimage import MetaImage
from annotationweb.models import Dataset, Task, Label
from segmentation.models import SegmentedImage
from django import forms
import os
from shutil import rmtree, copyfile


class SegmentationExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=True, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['dataset'] = forms.ModelMultipleChoiceField(queryset=Dataset.objects.filter(task=task))


class SegmentationExporter(Exporter):
    """
    asdads
    """

    task_type = Task.SEGMENTATION
    name = 'Default image segmentation exporter'

    def get_form(self, data=None):
        return SegmentationExporterForm(self.task, data=data)

    def export(self, form):

        datasets = form.cleaned_data['dataset']
        delete_existing_data = form.cleaned_data['delete_existing_data']
        # Create dir, delete old if it exists
        path = form.cleaned_data['path']
        if delete_existing_data:
            try:
                os.stat(path)
                rmtree(path)
            except:
                pass

            try:
                os.mkdir(path)
            except:
                return False, 'Failed to create directory at ' + path
        else:
            try:
                os.stat(path)
            except:
                return False, 'Path does not exist: ' + path


        # TODO non metaimage support
        segmented_images = SegmentedImage.objects.filter(task=self.task, image__dataset__in=datasets)
        for segmented_image in segmented_images:
            name = segmented_image.image.filename
            image_filename = name[name.rfind('/')+1:]
            dataset_path = os.path.join(path, segmented_image.image.dataset.name)
            try:
                os.mkdir(dataset_path)  # Make dataset path if doesn't exist
            except:
                pass

            # Copy image
            metaimage = MetaImage(filename=name)
            image_id = segmented_image.image.pk
            metaimage.write(os.path.join(dataset_path, str(image_id) + '.mhd'))

            # Copy all segmentation files
            segmentation_filename = os.path.join(PROJECT_PATH, os.path.join('segmentations', os.path.join(str(self.task.id), str(segmented_image.id) + '.mhd')))
            new_segmentation_filename = os.path.join(dataset_path, str(image_id) + '_segmentation.mhd')
            metaimage = MetaImage(filename=segmentation_filename)
            metaimage.write(new_segmentation_filename)


