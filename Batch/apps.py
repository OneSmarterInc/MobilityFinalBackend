import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.apps import AppConfig
from django.core.management import call_command
from datetime import datetime

scheduler = None  # global


def run_batch_reports():
    print("Running batch reports...", datetime.now())
    call_command("auto_send_batch_reports")


def run_notifications():
    print("Running notifications...", datetime.now())
    call_command("send_notification")


class BatchConfig(AppConfig):
    name = "Batch"

    def ready(self):
        global scheduler
        if scheduler and scheduler.running:
            return

        from django.conf import settings

        scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

        scheduler.add_job(
            run_batch_reports,
            trigger=CronTrigger(hour=1, minute=0),
            id="batch_reports",
            replace_existing=True,
        )

        scheduler.add_job(
            run_notifications,
            trigger=CronTrigger(hour=22, minute=0),
            id="notifications",
            replace_existing=True,
        )

        # scheduler.add_job(run_notifications, "interval",seconds=10, id="test_job")


        scheduler.start()

        atexit.register(lambda: scheduler.shutdown())
