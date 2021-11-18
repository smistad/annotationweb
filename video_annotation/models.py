from django.db import models
from annotationweb.models import KeyFrameAnnotation, Label


class VideoAnnotation(models.Model):
    image = models.ForeignKey(KeyFrameAnnotation, on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    label = models.ForeignKey(Label, on_delete=models.CASCADE)
