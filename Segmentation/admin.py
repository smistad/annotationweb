from django.contrib import admin

from .models import *

admin.site.register(SegmentationTask)
admin.site.register(SegmentationLabel)
admin.site.register(SegmentedImage)
