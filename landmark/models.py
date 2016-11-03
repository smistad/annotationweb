from django.db import models
from annotationweb.models import ProcessedImage, Label


class Landmark(models.Model):
    image = models.ForeignKey(ProcessedImage, on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    label = models.ForeignKey(Label)
