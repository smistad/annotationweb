from django.db import models
from annotationweb.models import KeyFrameAnnotation, Label


class ControlPoint(models.Model):
    image = models.ForeignKey(KeyFrameAnnotation, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    index = models.PositiveIntegerField()
    label = models.ForeignKey(Label)
    object = models.PositiveIntegerField()
    uncertain = models.BooleanField()
