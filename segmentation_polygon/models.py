from django.db import models
from annotationweb.models import ProcessedImage

class SegmentationPolygon(models.Model):
    image = models.OneToOneField(ProcessedImage, on_delete=models.CASCADE)
    target_frames = models.TextField()

class ControlPoint(models.Model):
    segmentation = models.ForeignKey(SegmentationPolygon, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    index = models.PositiveIntegerField()
    frame = models.PositiveIntegerField()
    object = models.PositiveIntegerField()
    uncertain = models.BooleanField()
