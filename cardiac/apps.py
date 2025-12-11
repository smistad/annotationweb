from django.apps import AppConfig
from common.config import TaskConfig


class CardiacConfig(AppConfig, TaskConfig):
    name = 'cardiac'

    @property
    def task_name(self):
        return 'Cardiac Apical 2CH/4CH Segmentation'
