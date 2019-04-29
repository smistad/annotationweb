from django.db import models
from annotationweb.models import ProcessedImage, Label


class ControlPoint(models.Model):
    image = models.ForeignKey(ProcessedImage, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    index = models.PositiveIntegerField()
    label = models.ForeignKey(Label)
    uncertain = models.BooleanField()
