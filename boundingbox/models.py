from django.db import models
from annotationweb.models import Annotation, Label


class BoundingBox(models.Model):
    image = models.ForeignKey(Annotation, on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    label = models.ForeignKey(Label)

