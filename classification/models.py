from django.db import models
from annotationweb.models import ProcessedImage, Label


class ImageLabel(models.Model):
    image = models.ForeignKey(ProcessedImage, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)

    def __str__(self):
        return self.image.image.filename + ' with label ' + self.label.name + ' created on ' + self.image.date.strftime('%Y-%m-%d %H:%M')



