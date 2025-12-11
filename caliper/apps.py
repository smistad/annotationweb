from django.apps import AppConfig
from common.config import TaskConfig


class CaliperConfig(AppConfig, TaskConfig):
    name = 'caliper'

    @property
    def task_name(self):
        return 'Caliper'
