from django.db import models
from Annotation.models import *
from Segmentation.models import *


class BoundingBoxTask(models.Model):
    name = models.CharField(max_length=200)
    dataset = models.ManyToManyField(Dataset)
    label = models.ManyToManyField(SegmentationLabel)

    def __str__(self):
        return self.name


class CompletedImage(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    task = models.ForeignKey(BoundingBoxTask, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)


class BoundingBox(models.Model):
    image = models.ForeignKey(CompletedImage, on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()

