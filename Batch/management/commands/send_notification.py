
from django.core.management.base import BaseCommand
from Batch.models import Notification
from OnBoard.Ban.models import BatchAutomation
from django.utils import timezone

VALID_DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

def is_batch_today(ba, now=None) -> bool:
    """
    Minimal check:
    - DAILY/WEEKLY: true if today's weekday has production=True
    - SPECIFIC: same, but you probably configured just one day anyway
    """
    if now is None:
        now = timezone.now()
    weekday = now.strftime("%A")  # e.g. "Monday"

    # Map days -> production flag
    day_map = {}
    for d in (ba.days or []):
        day = d.get("day")
        if day in VALID_DAYS:
            day_map[day] = bool(d.get("production"))

    return bool(day_map.get(weekday, False))

class Command(BaseCommand):
    help = "Create 'batch runs today' notifications for organizations that run today."

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()
        created = 0

        for ba in BatchAutomation.objects.all():
            if not is_batch_today(ba, now):
                continue

            # Avoid duplicates for the same org on the same day
            if Notification.objects.filter(company_id=ba.company_id, created_at__date=today).exists():
                continue

            Notification.objects.create(
                company_id=ba.company_id,
                description="Batch report runs today. Please complete bill payments before 10 PM."
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} notifications"))