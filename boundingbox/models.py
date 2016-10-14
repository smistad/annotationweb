from django.db import models
from annotationweb.models import ProcessedImage, Label


class BoundingBox(models.Model):
    image = models.ForeignKey(ProcessedImage, on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    label = models.ForeignKey(Label)

