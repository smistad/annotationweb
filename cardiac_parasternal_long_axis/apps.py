from django.apps import AppConfig
from common.config import TaskConfig


class CardiacParasternalLongAxisConfig(AppConfig, TaskConfig):
    name = 'cardiac_parasternal_long_axis'

    @property
    def task_name(self):
        return 'Cardiac Parasternal Long Axis Segmentation'
