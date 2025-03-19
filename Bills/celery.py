from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Bills.settings')

app = Celery('Bills')  # Ensure the app name matches your project name
app.config_from_object(settings, namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(['OnBoard',])  # Specify the apps explicitly if needed

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')