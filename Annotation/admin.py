from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Dataset)
admin.site.register(Image)
admin.site.register(Task)
admin.site.register(Label)
admin.site.register(LabeledImage)
admin.site.register(ImageSequence)
admin.site.register(KeyFrame)

