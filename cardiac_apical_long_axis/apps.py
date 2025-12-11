from django.apps import AppConfig
from common.config import TaskConfig


class CardiacApicalLongAxisConfig(AppConfig, TaskConfig):
    name = 'cardiac_apical_long_axis'

    @property
    def task_name(self):
        return 'Cardiac Apical Long Axis Segmentation'
