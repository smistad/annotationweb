from django.apps import AppConfig
from common.config import TaskConfig


class ImageQualityConfig(AppConfig, TaskConfig):
    name = 'image_quality'

    @property
    def task_name(self):
        return 'Image Quality'
