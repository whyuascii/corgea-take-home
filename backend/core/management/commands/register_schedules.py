from django.core.management.base import BaseCommand

from core.schedules import register_schedules


class Command(BaseCommand):
    help = "Register periodic django-q2 schedules and remove stale ones."

    def handle(self, *args, **options):
        register_schedules()
        self.stdout.write(self.style.SUCCESS("Periodic schedules registered."))
