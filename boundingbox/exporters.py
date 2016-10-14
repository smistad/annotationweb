from common.exporter import Exporter
from common.metaimage import MetaImage
from common.utility import create_folder
from annotationweb.models import ProcessedImage, Dataset, Task, Label
from boundingbox.models import BoundingBox
from django import forms
import os
from shutil import rmtree, copyfile


class BoundingBoxExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['dataset'] = forms.ModelMultipleChoiceField(queryset=Dataset.objects.filter(task=task))


class BoundingBoxExporter(Exporter):
    """
    asdads
    """

    task_type = Task.BOUNDING_BOX
    name = 'Default bounding box exporter'

    def get_form(self, data=None):
        return BoundingBoxExporterForm(self.task, data=data)

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

        images = ProcessedImage.objects.filter(task=self.task, image__dataset__in=datasets)
        for image in images:
            name = image.image.filename
            image_filename = name[name.rfind('/')+1:]
            create_folder(path)
            create_folder(os.path.join(path, 'images'))
            create_folder(os.path.join(path, 'labels'))

            # Copy image
            metaimage = MetaImage(filename=name)
            image_id = image.image.pk
            pil_image = metaimage.get_image()
            pil_image.save(os.path.join(path, os.path.join('images', str(image_id) + '.png')))

            # Write bounding boxes to labels folder
            boxes = BoundingBox.objects.filter(image=image)
            with open(os.path.join(path, os.path.join('labels', str(image_id) + '.txt')), 'w') as f:
                for box in boxes:
                    center_x = round(box.x + box.width*0.5)
                    center_y = round(box.y + box.height*0.5)
                    f.write('{} {} {} {}\n'.format(center_x, center_y, box.width, box.height))

        return True, path

