from django.db import models
from Annotation.models import *


class SegmentationLabel(models.Model):
    name = models.CharField(max_length=200)
    # Color stored as R G B with values from 0 to 255
    color_red = models.PositiveSmallIntegerField()
    color_green = models.PositiveSmallIntegerField()
    color_blue = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name


class SegmentationTask(models.Model):
    name = models.CharField(max_length=200)
    dataset = models.ManyToManyField(Dataset)
    label = models.ManyToManyField(SegmentationLabel)

    def __str__(self):
        return self.name


class SegmentedImage(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    task = models.ForeignKey(SegmentationTask, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

