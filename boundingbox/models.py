from django.db import models
from classification.models import *
from segmentation.models import *


class CompletedImage(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)


class BoundingBox(models.Model):
    image = models.ForeignKey(CompletedImage, on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    label = models.ForeignKey(Label)

