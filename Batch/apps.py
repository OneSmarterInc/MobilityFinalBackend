from django.apps import AppConfig


class BatchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Batch'

# from django.apps import AppConfig

# from apscheduler.schedulers.background import BackgroundScheduler
# from django.core.management import call_command
# import atexit

# def my_job():
#     print("Running batch reports...")
#     call_command("auto_send_batch_reports")

# class BatchConfig(AppConfig):
#     name = 'Batch'

#     def ready(self):
#         scheduler = BackgroundScheduler()
#         scheduler.add_job(my_job, 'interval', hours=3)  # every 3 hours
#         scheduler.start()

#         # Shut down the scheduler when Django stops
#         atexit.register(lambda: scheduler.shutdown())
