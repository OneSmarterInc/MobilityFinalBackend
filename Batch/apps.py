from django.apps import AppConfig


class BatchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Batch'

from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management import call_command
import atexit
from datetime import datetime

def run_batch_reports():
    print("Running batch reports...", datetime.now())
    call_command("auto_send_batch_reports")


def run_notifications():
    print("Running notifications...", datetime.now())
    call_command("send_notification")


# class BatchConfig(AppConfig):
#     name = 'Batch'

#     def ready(self):
#         scheduler = BackgroundScheduler()

#         scheduler.add_job(run_batch_reports, 'interval', hours=3)
#         scheduler.start()
#         atexit.register(lambda: scheduler.shutdown())

class BatchConfig(AppConfig):
    name = "Batch"

    def ready(self):
        scheduler = BackgroundScheduler()

        # Run auto_send_batch_reports daily at 10:00 PM
        scheduler.add_job(
            run_batch_reports,
            trigger=CronTrigger(hour=21, minute=10),
            id="batch_reports",
            replace_existing=True,
        )

        # Run send_notification daily at 1:00 AM
        scheduler.add_job(
            run_notifications,
            trigger=CronTrigger(hour=1, minute=0),
            id="notifications",
            replace_existing=True,
        )

        scheduler.start()

        atexit.register(lambda: scheduler.shutdown())