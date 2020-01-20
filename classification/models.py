from django.db import models
from annotationweb.models import KeyFrameAnnotation, Label


class ImageLabel(models.Model):
    image = models.OneToOneField(KeyFrameAnnotation, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.image.image_annotation.image) + ' with label ' + self.label.name + ' created on ' + self.image.image_annotation.date.strftime('%Y-%m-%d %H:%M')



