from django.apps import AppConfig
from common.config import TaskConfig


class SplineSegmentation(AppConfig, TaskConfig):
    name = 'spline_segmentation'

    @property
    def task_name(self):
        return 'Spline Segmentation'
